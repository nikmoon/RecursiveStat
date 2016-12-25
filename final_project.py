# эти строки введены для IDE, их нужно закомментировать или удалить
def getProductType(): pass
def getProductColor(): pass
def getProductCondition(): pass
def get_stat_api(): pass

"""
Список метрик и соответствующих им методов
"""
metrics = {
    'productType': {
        'method': getProductType,
        'name': 'productType',      # данное поле нужно использовать для названия вложенного поля
    },
    'productColor': {
        'method': getProductColor,
        'name': 'productColor',
    },
    'productCondition': {
        'method': getProductCondition,
        'name': 'productCondition',
    }
}


"""
Список веток
"""
branches = {
    'branch1': 'price==Low,condition==New',
    'branch2': 'price==Medium,color==Red',
    'branch3': 'color==Blue,price==High',
}


def getStatistics(strStats, values, globalFilter, limit=None, offset=None):
    """
    :param strStats: 'productType;branch1;productColor;branch2;branch3;productCondition'
    :param values: 'sklad1,sklad2'
    :param globalFilter: ''
    :param limit:
    :param offset:
    :return:
    """

    def getRecursive(lvl=0, listStatFilter=[], statIndex=0):
        """
        :param lvl: текущий уровень вложенности
        :param listStatFilter: список предыдущих метрик, для которых получены статистики
        :return: Возвращается список из двух элементов: ['имя метрики', [список статистик для метрики]]
            Например: ['productType', [{'label': 'Окна', 'segment': 'productType==Окна',...}, {...}, ...]

        listStats и listValues берутся из внешней функции
        """
        # условие выхода из рекурсии - необходимо для случая, когда listStats изначально пустой
        if statIndex == len(listStats):
            return None

        # формируем фильтр
        filter = ';'.join(listStatFilter + globalFilter)

        # берем очередную метрику, для которой нужна статистика
        curStat = listStats[statIndex]

        listBranches = []
        nameMetric = None

        # если текущая метрика - branch
        if curStat.startswith('branch'):
            nameMetric = 'branch'
            listBranches.append(curStat)

            # выбираем все идущие подряд бранчи
            while statIndex < (len(listStats) - 1):
                statIndex += 1
                if not listStats[statIndex].startswith('branch'):
                    statIndex -= 1
                    break
                listBranches.append(listStats[statIndex])

            listBranches.append('All data')     # для ветки 'All data'

            # здесь мы имеем список с названиями бранчей, можно получить статистику для них
            # используя пакетную обработку
            list_of_queries = []
            for branch in listBranches:
                list_of_queries.append({
                    'method': 'branch',     # значение указыает на то, что это запрос для бранча
                    'branch': branch,
                    'values': values,
                    'filter': filter,
                    'limit': None,          # limit и offset тоже не имеют смысла в данной ветке
                    'offset': None,
                })

            # запрашиваем статистики для указанных веток
            # для каждого запроса из списка должен возвращаться один словарь
            data = [item[0] for item in get_stat_api(list_of_queries)]

            # если в списке нужных метрик больше нет, возвращаем результат наверх
            if statIndex == (len(listStats) - 1):
                return [nameMetric, data]

        # если текущая метрика - обычная, например 'productType'
        else:
            nameMetric = metrics[curStat]['name']
            list_of_queries = [{
                'method': metrics[nameMetric]['method'],
                'values': values,
                'filter': filter,
                'limit': limit if lvl == 0 else None,
                'offset': offset if lvl == 0 else None,
            }]
            data = get_stat_api(list_of_queries)[0]

        # условие выхода из рекурсии - достигнут конец списка listStats
        if (statIndex + 1) == len(listStats):
            return [nameMetric, data]

        # здесь у нас есть список статистик в data и соответствующее им название метрики
        for item in data:

            # если текущий элемент не имеет поля 'segment', для него рекурсия закончена - он последний в цепочке
            if not 'segment' in item:
                continue

            result = getRecursive(lvl + 1, listStatFilter + [item['segment']], statIndex + 1)

            # вот здесь result[0] как раз равно metrics[metricName]['name']
            item[result[0]] = result[1]

        return [nameMetric, data]

    # преобразовываем строку с необходимыми статистиками в список
    listStats = strStats.replace(' ', '').split(';')

    x = 1

    return {
        'stats': getRecursive()[1],
    }
