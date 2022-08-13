from collections import defaultdict
import os
from specInfo import *
import re
import datetime

class BatchData:
    def __init__(self, batchpath, specpath):
        self.batchpath = batchpath
        self.specpath = specpath
        self.specInfo = MetaData()
        self.makeSpecData()

    # spec 정보를 만드는 부분
    def makeSpecData(self):
        self.specInfo.getSpecInfoByDirectory(self.specpath)
        self.specInfo.getTrInfoByDirectory(self.specpath)

    def convertBatchLog(self, trcdlst=None):
        convertedBatchLog = defaultdict(dict)
        mapCdToNm = dict()
        try:
            with open(self.batchpath) as f:
                for line in f:
                    sub_result = dict()
                    trCd = line[9:14]
                    if trCd in trcdlst:  # 타겟이 되는 종목코드만 조회한다.
                        try:
                            trNm = self.specInfo.totalTrDict[trCd]['TR명']
                        except:
                            print(f'코드\'{trCd}\'의 정보가 없습니다.')
                            continue
                        idx = 9
                        byte_line = line.encode('euc-kr')
                        for name, _len in self.specInfo.totalSpecDict[trNm]:
                            mark = byte_line[idx: idx + int(_len)]
                            sub_result[name] = mark.decode('euc-kr').rstrip()
                            if name == '종목코드':
                                insCd = sub_result[name]
                            if name in ('종목한글명', '한글종목명', '종목한글약명'):
                                insNm = sub_result[name]
                                mapCdToNm[insNm] = insCd # 이름을 키 값으로 저장, 더 빠르게 조회
                            idx += int(_len)
                        #convertedBatchLog[trCd][insCd] = sub_result  # 결과를 저장하는 곳 TR의 정보를 굳이 저장할 필요가 없음
                        convertedBatchLog[insCd] = sub_result  # 결과를 저장하는 곳

        except Exception as e:
            print(e)
            pass
        return convertedBatchLog, mapCdToNm


class OptionObject:
    def __init__(self, rawData):
        self.rawData = rawData
        self.insCd = None
        self.insNm = None
        self.mappDataWithfield()

    def metaInfoManager(self):  # metaData를 관리하는 곳
        metaData = {'종목코드': "insCd", '종목한글명': "insNm"}
        return metaData

    # 메타정보에 맞춰 rawData와 변수를 매핑해주는 곳
    def mappDataWithfield(self):
        metaData = self.metaInfoManager()
        for key, value in metaData.items():
            exec(f'self.{value} = \'{self.rawData[key]}\'')


class FutureObject:
    def __init__(self, rawData):
        self.rawData = rawData
        self.insCd = None
        self.insNm = None
        self.mappDataWithfield()

    def getMetaInfo(self):
        metaData = {'종목코드': "insCd", '종목한글명': "insNm"}
        return metaData

    def mappDataWithfield(self):
        metaData = self.getMetaInfo()
        for key, value in metaData.items():
            exec(f'self.{value} = \'{self.rawData[key]}\'')


class EquityObject:
    def __init__(self, rawData):
        self.rawData = rawData
        self.insCd = None
        self.insNm = None
        self.mappDataWithfield()

    def getMetaInfo(self):
        # dictionay에 매핑된 정보와 변수를 매핑한다 ('한글로 된 정보': 변수명')
        metaData = {'종목코드': "insCd", '종목한글약명': "insNm"}
        return metaData

    def mappDataWithfield(self):
        metaData = self.getMetaInfo()
        for key, value in metaData.items():
            exec(f'self.{value} = \'{self.rawData[key]}\'')


class OptionLoader:
    def __init__(self, batchpath=None, specpath=None):
        self.batchData = BatchData(batchpath, specpath)
        self.stockBatchLog, self.stockCdNm = None, dict()
        self.loadData()
        self.matList = None

    def loadData(self):
        opStockTrcd = ['A0184', 'A0034', 'A0025', 'A0134', 'A0174']
        self.stockBatchLog, self.stockCdNm = self.batchData.convertBatchLog(opStockTrcd)

    # 월물에 대한 정보를 담는 곳
    def getMatlist(self, insId, _date=None):
        # 날짜에 대한 정보가 담겨 있어야 됨
        date = _date if _date else datetime.today()
        self.matList = dict()
        for key, value in self.stockBatchLog.items():
            if value['기초자산코드'] == insId and value['만기일자'] > date:
                self.matList[value['만기일자']] = value
        self.matList = sorted(self.matList.items(), key=lambda item: item[0], reverse=True)
        return self.matList

    def stockInfo(self, _input=None):
        insCd = self.getInsCd(_input)
        optionObject = OptionObject(self.stockBatchLog[insCd])
        return optionObject


class FutureLoader:
    def __init__(self, batchpath=None, specpath=None):
        self.batchData = BatchData(batchpath, specpath)
        self.stockBatchLog, self.stockCdNm = None, dict()
        self.loadData()

    def loadData(self):
        fuStockTrcd = ['A0014', 'A0164', 'A0015', 'A0124', 'A0094', 'A0104', 'A0024']
        self.stockBatchLog, self.stockCdNm = self.batchData.convertBatchLog(fuStockTrcd)

    def getInsCd(self, _input):
        insCdType = re.compile(r'[a-zA-Z0-9]*').search(_input).group()
        insCd = _input if _input == insCdType else self.stockCdNm[_input]
        return insCd

    def stockInfo(self, _input, ):
        insCd = self.getInsCd(_input)
        futureObject = FutureObject(self.stockBatchLog[insCd])
        return futureObject


class EquityLoader:
    def __init__(self, batchpath=None, specpath=None):
        self.batchData = BatchData(batchpath, specpath)
        self.stockBatchLog, self.stockCdNm = None, dict()
        self.loadData()

    def loadData(self):
        eqStockTrcd = ['A0011', 'A0012']
        self.stockBatchLog, self.stockCdNm = self.batchData.convertBatchLog(eqStockTrcd)

    def getInsCd(self, _input):
        insCdType = re.compile(r'[a-zA-Z0-9]*').search(_input).group()
        insCd = _input if _input == insCdType else self.stockCdNm[_input]
        return insCd

    def stockInfo(self, _input):
        insCd = self.getInsCd(_input)
        equityObject = EquityObject(self.stockBatchLog[insCd])
        return equityObject


if __name__ == "__main__":

    main_path = 'C:/Users/USER/Downloads/mm/자료/시세, 배치정보'
    feed_spec = os.path.join(main_path, "feed spec")
    feed_file = os.path.join(main_path, "feed file/20220803.batch.log")

    spec = MetaData()
    totalSpecDf, totalSpec = spec.getSpecInfoByDirectory(main_path + '/feed spec')
    totalTr = spec.getTrInfoByDirectory(main_path + '/feed spec')

    optionLoader = OptionLoader(batchpath=feed_file, specpath=feed_spec)
    futureLoader = FutureLoader(batchpath=feed_file, specpath=feed_spec)
    equityLoader = EquityLoader(batchpath=feed_file, specpath=feed_spec)

    option = optionLoader.stockInfo('KR4211S80342')
    future = futureLoader.stockInfo('KR4101S90005')
    equity = equityLoader.stockInfo('HK0000057197')
    equity_nm = equityLoader.stockInfo('이스트아시아홀딩스')

    print(option.insCd, option.insNm)
    print(future.insCd, future.insNm)
    print(equity.insCd, equity.insNm)
    print(equity_nm.insCd, equity_nm.insNm)
