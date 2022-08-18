from collections import defaultdict
import os
from specInfo import *
import re
from _datetime import datetime
from DTO import *
from DAO import *


class BatchlogManager:
    def __init__(self, batchpath, specpath):
        self.batchpath = batchpath
        self.specpath = specpath
        self.specInfo = MetaData()
        self.makeSpecData()

    # spec 정보를 만드는 부분
    def makeSpecData(self):
        self.specInfo.getSpecInfoByDirectory(self.specpath)
        self.specInfo.getTrInfoByDirectory(self.specpath)

    def convertBatchlogToJson(self, trcdlst=None, inisType=None):
        convertedBatchLog = defaultdict(dict)
        mapCdToNm = dict()
        with open(self.batchpath, encoding='cp949') as f:
            for line in f:
                trCd, trNm, idx, sub_result = line[9:14], None, 9, dict()
                if trCd in trcdlst:
                    try:
                        trNm = self.specInfo.totalTrDict[trCd]['TR명']
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

                    if inisType == 'OP':
                        dto = OptionDTO(sub_result)
                        dao = OptionDAO(dto)
                    elif inisType == 'FU':
                        dto = FutureDTO(sub_result)
                        dao = FutureDAO(dto)
                    elif inisType == 'EQ':
                        dto = EquityDTO(sub_result)
                        dao = EquityDAO(dto)

                    db.session.add(dao)
        try:
            db.session.commit()
        except:
            print("중복된 데이터가 존재합니다.")
            pass
        return convertedBatchLog, mapCdToNm


class OptionLoader:
    def __init__(self, batchpath=None, specpath=None):
        self.batchlogManager = BatchlogManager(batchpath, specpath)
        self.stockBatchLog, self.stockCdNm = None, dict()  # 종목 정보
        self.getBatchlog()

    def getBatchlog(self):
        opStockTrcd = ['A0184', 'A0034', 'A0025', 'A0134', 'A0174']
        self.stockBatchLog, self.stockCdNm = self.batchlogManager.convertBatchlogToJson(opStockTrcd, 'OP')

    def getMaturitylist(self, insId, callput, atmCd=None, _date=None): # atmcd = O1, I2, A2
        date = _date if _date else datetime.today().strftime("%Y%m%d")
        self.matList = defaultdict(list)
        var_CP = '42' if callput == 'C' else '43'  # call, put 관리
        var_ATM = 3 if atmCd[0] == 'O' else 2 if atmCd[0] == 'I' else 1   # 0:선물, 1:ATM, 2:ITM, 3:OTM
        for inisCd, value in self.stockBatchLog.items():
            if value['기초자산종목코드'] == insId and value['종목코드'][2:4] == var_CP \
                and value['ATM구분코드'] == str(var_ATM) and value['만기일자'] > date:
                optionOBJ = OptionDTO(value)
                self.matList[value['만기일자']].append(optionOBJ)

        # 내부에서는 행사가 기준으로 정렬
        revs = True if atmCd[0] == 'O' else False
        for v in self.matList.values():
            v.sort(key=lambda x: x.strike, reverse=revs)
        matList = sorted(self.matList.items(), key=lambda x: x[0])  # 만기일자, 행사가 기준 정렬
        # [('만기일자', [option1, option2, ... ]), ... ]
        return matList

    def stockInfoByOtherInfo(self, insId=None, matidx=None, callput=None, atmCd=None):
        try:
            matList = self.getMaturitylist(insId, callput, atmCd)
        except:
            print("기초자산에 대한 정보가 없습니다.")
            return
        if matidx == 'last' or matidx == -1:  # 원월물 인덱스 자동 설정
            matidx = len(matList)-1
        matDt, optionOBJLst = matList[matidx][0], matList[matidx][1]  # 특정 만기에 해당하는 요소
        atmIdx = int(atmCd[1:])
        optionObject = optionOBJLst[atmIdx]  # 행사가 순으로 나열된 배열
        return optionObject

    def getOptionListSoredByStrike(self, insId=None, matidx=None, callput=None, atmCd=None):
        try:
            matList = self.getMaturitylist(insId, callput, atmCd)
        except:
            print("기초자산에 대한 정보가 없습니다.")
            return
        if matidx == 'last' or matidx == -1:  # 원월물 인덱스 자동 설정
            matidx = len(matList) - 1
        matDt, optionOBJLst = matList[matidx][0], matList[matidx][1]  # 특정 만기에 해당하는 요소
        opList = [[op.inisCd, op.inisNm, op.strike] for op in optionOBJLst]
        return opList

    def getInisCd(self, _input):
        inisCdType = re.compile(r'[a-zA-Z0-9]*').search(_input).group()
        inisCd = _input if _input == inisCdType else self.stockCdNm[_input]
        return inisCd

    def getStockInfo(self, _input):
        inisCd = self.getInisCd(_input)
        optionObject = OptionDTO(self.stockBatchLog[inisCd])
        return optionObject

    # 특정 종목의 반대편 옵션 주기
    def getOpstPosition(self, inisCd):
        try:
            optionObj = self.getStockInfo(inisCd)
        except:
            print("종목에 대한 정보가 없습니다.")
            return
        for inisCd, value in self.stockBatchLog.items():
            target = OptionDTO(value)
            if target.insCd == optionObj.insCd and target.posType != optionObj.posType\
                and target.matDt == optionObj.matDt and target.strike == optionObj.strike:
                return OptionDTO(value)


class FutureLoader:
    def __init__(self, batchpath=None, specpath=None):
        self.batchlogManager = BatchlogManager(batchpath, specpath)
        self.stockBatchLog, self.stockCdNm = None, dict()
        self.getBatchlog()

    def getBatchlog(self):
        fuStockTrcd = ['A0014', 'A0164', 'A0015', 'A0124', 'A0094', 'A0104', 'A0024']
        self.stockBatchLog, self.stockCdNm = self.batchlogManager.convertBatchlogToJson(fuStockTrcd, 'FU')

    # 특정 기초자산의 월물에 대한 정보를 담는 곳
    def getMaturitylist(self, insId, _date=None):
        date = _date if _date else datetime.today().strftime("%Y%m%d")
        matList = list()
        for inisCd, value in self.stockBatchLog.items():
            if value['기초자산종목코드'] == insId and value['만기일자'] > date:
                matList.append((inisCd, value['만기일자']))
        matList = sorted(matList, key=lambda x: x[1])  # (inisCd, 만기일자)로 이뤄진 리스트를 만기일자를 기준으로 정렬
        return matList

    def getStockInfo(self, insId=None, matidx=None):  # 월물 정보만 필요
        matList = self.getMaturitylist(insId)
        if len(matList) == 0:
            return "종목정보가 없습니다."
        if matidx == 'last' or matidx == -1:  # 원월물 인덱스 자동 설정
            matidx = len(matList)-1
        inisCd = matList[matidx][0]
        futureObject = FutureDTO(self.stockBatchLog[inisCd])
        return futureObject


class EquityLoader:
    def __init__(self, batchpath=None, specpath=None):
        self.batchlogManager = BatchlogManager(batchpath, specpath)
        self.stockBatchLog, self.stockCdNm = None, dict()
        self.getBatchlog()

    def getBatchlog(self):
        eqStockTrcd = ['A0011', 'A0012']
        self.stockBatchLog, self.stockCdNm = self.batchlogManager.convertBatchlogToJson(eqStockTrcd, 'EQ')

    def getInsCd(self, _input):
        insCdType = re.compile(r'[a-zA-Z0-9]*').search(_input).group()
        insCd = _input if _input == insCdType else self.stockCdNm[_input]
        return insCd

    def getStockInfo(self, _input):
        insCd = self.getInsCd(_input)
        equityObject = EquityDTO(self.stockBatchLog[insCd])
        return equityObject


if __name__ == "__main__":

    main_path = '..'
    feed_spec = os.path.join(main_path, "feed spec")
    feed_file = os.path.join(main_path, "feed file/20220803.batch.log")

    spec = MetaData()
    totalSpecDf, totalSpec = spec.getSpecInfoByDirectory(main_path + '/feed spec')
    totalTr = spec.getTrInfoByDirectory(main_path + '/feed spec')

    with app.app_context(): # Db세션을 연결해야됨
        db.create_all()  # 선언했던 테이블 생성해줘야됨
        optionLoader = OptionLoader(batchpath=feed_file, specpath=feed_spec)
        # futureLoader = FutureLoader(batchpath=feed_file, specpath=feed_spec)
        # equityLoader = EquityLoader(batchpath=feed_file, specpath=feed_spec)
        option = optionLoader.stockInfoByOtherInfo('KR7005930003', 0, 'C', 'I1')  # 기초자산ID, 월물정보, callput, ATM정보
        option = optionLoader.stockInfoByOtherInfo('KR7005930003', 1, 'C', 'I1')  # 기초자산ID, 월물정보, callput, ATM정보
        optionList = optionLoader.getOptionListSoredByStrike('KR7005930003', 0, 'C', 'I')  # 기초자산ID, 월물정보, callput, ATM정보

        position = optionLoader.getStockInfo('KR4323T30314')  # 포지션
        opstposition = optionLoader.getOpstPosition('KR4323T30314')  # 반대 포지션
        # future = futureLoader.stockInfo('KR4101S90005')  # 기초자산ID, 월물정보
        # equity = equityLoader.stockInfo('HK0000057197')
        # equity_nm = equityLoader.stockInfo('이스트아시아홀딩스')

        print(option.inisCd, option.inisNm)
        print(optionList)
        print(position.inisCd, position.inisNm, position.strike)
        print(opstposition.inisCd, opstposition.inisNm, position.strike)
        # print(future.inisCd, future.inisNm)
        # print(equity.inisCd, equity.inisNm)
        # print(equity_nm.inisCd, equity_nm.inisNm)

    '''
    # 과제 2 : 종목정보 모듈 제작

- 소과제 1 : 종목정보 제공하는 기능 구현

  * 현물의 경우 종목코드나 종목명이 주어지면 종목정보를 반환

  * 파생상품의 경우 기초자산ID, 월물 정보 (옵션의 경우 OTM, ITM, ATM 몇번째인지까지, call/put)가 주어지면 종목정보를 반환
  ATM구분코드  
  * 기타 자주 사용하는 기능 구현 
  (근월물 요청, -> 0 입력시
  원월물 요청, -> last or -1 입력시 
  행사가순 옵션 리스트,  -> # 기초자산ID, 월물정보, callput, ATM정보
  반대편 옵션 (콜 -> 풋, 풋 -> 콜) -> 종목코드가 주어졌을 때 
  )
 
    '''
