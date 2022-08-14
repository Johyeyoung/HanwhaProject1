from collections import defaultdict
import os
from specInfo import *
import re
from _datetime import datetime

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
            with open(self.batchpath, encoding='cp949') as f:
                for line in f:
                    trCd, trNm, idx, sub_result = line[9:14], None, 9, dict()
                    if trCd in trcdlst:
                        try:
                            trNm = self.specInfo.totalTrDict[trCd]['TR명']

                            # if trCd in trcdlst:  # 타겟이 되는 종목코드만 조회한다.
                            #     if trCd in originTrcdlst:
                            #         trNm = self.specInfo.totalTrDict[trCd]['TR명']
                            # else:
                            #     print(f'코드\'{trCd}\'의 정보가 없습니다.')
                            #     continue
                        except:
                            print(f'코드\'{trCd}\'의 정보가 없습니다.')
                            continue

                        for name, _len in self.specInfo.totalSpecDict[trNm]:
                            byte_line = line.encode('euc-kr')
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
        self.inisCd = None
        self.inisNm = None
        self.insCd = None
        self.matDt = None
        self.atmCd = None
        self.mappDataWithfield()

    def metaInfoManager(self):  # metaData를 관리하는 곳
        metaData = {'종목코드': "inisCd", '종목한글명': "inisNm", '기초자산종목코드': 'insCd', '만기일자': 'matDt', 'ATM구분코드': 'atmCd'}
        return metaData

    # 메타정보에 맞춰 rawData와 변수를 매핑해주는 곳
    def mappDataWithfield(self):
        metaData = self.metaInfoManager()
        for key, value in metaData.items():
            exec(f'self.{value} = \'{self.rawData[key]}\'')


class FutureObject:
    def __init__(self, rawData):
        self.rawData = rawData
        self.inisCd = None
        self.inisNm = None
        self.insCd = None
        self.matDt = None
        self.mappDataWithfield()

    def getMetaInfo(self):
        metaData = {'종목코드': "inisCd", '종목한글명': "inisNm", '기초자산종목코드': 'insCd', '만기일자': 'matDt'}
        return metaData

    def mappDataWithfield(self):
        metaData = self.getMetaInfo()
        for key, value in metaData.items():
            exec(f'self.{value} = \'{self.rawData[key]}\'')


class EquityObject:
    def __init__(self, rawData):
        self.rawData = rawData
        self.inisCd = None
        self.inisNm = None
        self.mappDataWithfield()

    def getMetaInfo(self):
        # dictionay에 매핑된 정보와 변수를 매핑한다 ('한글로 된 정보': 변수명')
        metaData = {'종목코드': "inisCd", '종목한글약명': "inisNm"}
        return metaData

    def mappDataWithfield(self):
        metaData = self.getMetaInfo()
        for key, value in metaData.items():
            exec(f'self.{value} = \'{self.rawData[key]}\'')


class OptionLoader:
    def __init__(self, batchpath=None, specpath=None):
        self.batchData = BatchData(batchpath, specpath)
        self.stockBatchLog, self.stockCdNm = None, dict()  # 종목 정보
        self.loadData()

    def loadData(self):
        opStockTrcd = ['A0184', 'A0034', 'A0025', 'A0134', 'A0174']
        self.stockBatchLog, self.stockCdNm = self.batchData.convertBatchLog(opStockTrcd)

    # 특정 기초자산의 월물에 대한 정보를 담는 곳
    def getMaturitylist(self, insId, atmCd=None, _date=None):
        date = _date if _date else datetime.today().strftime("%Y%m%d")
        self.matList = list()
        for inisCd, value in self.stockBatchLog.items():
            # 기초자산종목코드, atm구분코드 까지만 하면 유니크함 여기서 만기일자만 미정
            if value['기초자산종목코드'] == insId and value['ATM구분코드'] == str(atmCd) and value['만기일자'] > date:
                self.matList.append((inisCd, value['만기일자'], value['ATM구분코드']))
        matList = sorted(self.matList, key=lambda x: x[1])  # (inisCd, 만기일자)로 이뤄진 리스트를 만기일자를 기준으로 정렬
        return matList

    def stockInfo(self, insId=None, matidx=None, atmCd=None):
        matList = self.getMaturitylist(insId, atmCd)

        if len(matList) == 0:
            return "종목정보가 없습니다."

        if matidx == 'last' or matidx == -1:  # 원월물 인덱스 자동 설정
            matidx = len(matList)-1
        inisCd = matList[matidx][0]  # (inisCd, value['만기일자'], value['ATM구분코드'])
        optionObject = OptionObject(self.stockBatchLog[inisCd])
        return optionObject


class FutureLoader:
    def __init__(self, batchpath=None, specpath=None):
        self.batchData = BatchData(batchpath, specpath)
        self.stockBatchLog, self.stockCdNm = None, dict()
        self.loadData()

    def loadData(self):
        fuStockTrcd = ['A0014', 'A0164', 'A0015', 'A0124', 'A0094', 'A0104', 'A0024']
        self.stockBatchLog, self.stockCdNm = self.batchData.convertBatchLog(fuStockTrcd)

    # 특정 기초자산의 월물에 대한 정보를 담는 곳
    def getMaturitylist(self, insId, _date=None):
        date = _date if _date else datetime.today().strftime("%Y%m%d")
        self.matList = list()
        for inisCd, value in self.stockBatchLog.items():
            if value['기초자산종목코드'] == insId and value['만기일자'] > date:
                self.matList.append((inisCd, value['만기일자']))
        matList = sorted(self.matList, key=lambda x: x[1])  # (inisCd, 만기일자)로 이뤄진 리스트를 만기일자를 기준으로 정렬
        return matList

    def stockInfo(self, insId=None, matidx=None):  # 월물 정보만 필요
        matList = self.getMaturitylist(insId)
        if len(matList) == 0:
            return "종목정보가 없습니다."
        if matidx == 'last' or matidx == -1:  # 원월물 인덱스 자동 설정
            matidx = len(matList)-1
        inisCd = matList[matidx][0]
        futureObject = FutureObject(self.stockBatchLog[inisCd])
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

    main_path = '..'
    feed_spec = os.path.join(main_path, "feed spec")
    feed_file = os.path.join(main_path, "feed file/20220803.batch.log")

    spec = MetaData()
    totalSpecDf, totalSpec = spec.getSpecInfoByDirectory(main_path + '/feed spec')
    totalTr = spec.getTrInfoByDirectory(main_path + '/feed spec')

    optionLoader = OptionLoader(batchpath=feed_file, specpath=feed_spec)
    # futureLoader = FutureLoader(batchpath=feed_file, specpath=feed_spec)
    # equityLoader = EquityLoader(batchpath=feed_file, specpath=feed_spec)

    option = optionLoader.stockInfo('KR7005930003', 0, 1)  # 기초자산ID, 월물정보드 KR7005930003
    # future = futureLoader.stockInfo('KR4101S90005')  # 기초자산ID, 월물정보
    # equity = equityLoader.stockInfo('HK0000057197')
    # equity_nm = equityLoader.stockInfo('이스트아시아홀딩스')

    print(option.inisCd, option.inisNm)
    # print(future.inisCd, future.inisNm)
    # print(equity.inisCd, equity.inisNm)
    # print(equity_nm.inisCd, equity_nm.inisNm)

    '''
    # 과제 2 : 종목정보 모듈 제작

- 소과제 1 : 종목정보 제공하는 기능 구현

  * 현물의 경우 종목코드나 종목명이 주어지면 종목정보를 반환

  * 파생상품의 경우 기초자산ID, 월물 정보 (옵션의 경우 OTM, ITM, ATM 몇번째인지까지)가 주어지면 종목정보를 반환

  * 기타 자주 사용하는 기능 구현 
  (근월물 요청, 0
  원월물 요청, 0
  ATM Option,  
  행사가순 옵션 리스트, 
  반대편 옵션 (콜 -> 풋, 풋 -> 콜) 
  등)

- 소과제 2 : 종목정보 DB에 저장

  * 옵션 제외

  * 현물은 기준가 (ETF는 NAV)

  * 선물은 연속월물을 정의하고 연속월물 기반으로 DB에 종목정보 저장

  * 선물은 잔존만기(일수), 기준가
    '''
