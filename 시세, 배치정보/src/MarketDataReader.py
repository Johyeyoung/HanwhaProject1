from collections import defaultdict
import os
from specInfo import *
import re
from _datetime import datetime
from DTO import *
from DAO import *



class BatchlogManager:
    def __init__(self, batchpath, metadata_path):
        self.batchpath = batchpath
        self.metadata_path = metadata_path

    # TR코드와 SPEC 정보를 산출하는 부분
    def getSpecInfo(self, metadata_path):
        specInfo = MetaData()
        specInfo.getSpecInfoByDirectory(metadata_path)
        specInfo.getTrInfoByDirectory(metadata_path)
        return specInfo

    def bulkinsertDAL(self, total_result, inisType, baseDt):
        table, dao = None, None
        for sub_result in total_result.values():
            if inisType == 'Option':
                dto = OptionDTO(sub_result)
                dto.baseDt = baseDt
                dao = OptionDAO(dto)
                table = OptionDAO

            elif inisType == 'Future':
                dto = FutureDTO(sub_result)
                dao = FutureDAO(dto)

            elif inisType == 'Equity':
                dto = EquityDTO(sub_result)
                dao = EquityDAO(dto)

            elif inisType == 'UNDER':
                dto = UnderlyingDTO(sub_result)
                dao = UnderlyingDAO(dto)
                table = UnderlyingDAO
            try:
                db.session.add(dao)
                db.session.commit()
            except:
                print("중복된 데이터가 존재합니다.")
                db.session.rollback()
        #
        #
        # try:
        #     db.session.commit()
        # except:
        #     print("중복된 데이터가 존재합니다.")
        #     db.session.rollback()
        #     obj = db.session.query(table).filter((table.baseDt == baseDt)| (table.baseDt == '00000000'))
        #     for i in obj:
        #         db.session.delete(i)
        #     db.session.commit()
        #     self.bulkinsertDAL(total_result, inisType, baseDt)


    def provideParsingdata(self, line, metainfoDict, start_idx=0):
        idx, result, inisCd, inisNm, baseDt = start_idx, dict(), None, None, None
        underlying = dict()
        for key, v_len in metainfoDict:
            byte_line = line.encode('euc-kr')
            value = byte_line[idx: idx + int(v_len)]
            result[key] = value.decode('euc-kr').rstrip()
            idx += int(v_len)

            if key == '종목코드':
                inisCd = result[key]
            if key in ('종목한글명', '한글종목명', '종목한글약명'):
                inisNm = result[key]
            if key == '영업일자(입회일자)':
                baseDt = result[key]
                underlying[key] = result[key]
            if '기초자산' in key:
                underlying[key] = result[key]

        return result, inisCd, inisNm, baseDt, underlying


    # 실제로 SPEC를 토대로 배치파일의 내용을 파싱하는 부분
    def run(self, trcdlst=None, inisType=None):
        total_Result = defaultdict(dict)
        metaCdNm = dict()
        underlyingInfo = dict()
        specInfo = self.getSpecInfo(self.metadata_path)

        with open(self.batchpath, encoding='cp949') as f:
            for line in f:
                try:
                    trCd = line[9:14] if line[9:14] in trcdlst else None
                    trNm = specInfo.totalTrDict[trCd]['TR명']
                except:
                    #print(f'코드\'{line[9:14]}\'의 정보가 없습니다.')
                    continue
                metaInfo = specInfo.totalSpecDict[trNm]
                sub_result, inisCd, inisNm, baseDt, underlying = self.provideParsingdata(line, metaInfo, 9)
                metaCdNm[inisNm] = inisCd  # 이름을 키 값으로 저장, 더 빠르게 조회
                total_Result[inisCd] = sub_result  # 종목의 전체 결과를 저장하는 곳
                if inisType in ('Option', 'Future'):
                    underlyingInfo[sub_result['기초자산ID']] = underlying  # 기초자산의 정보를 저장하는 곳

        if inisType in ('Option', 'Future'):
            pass
            self.bulkinsertDAL(underlyingInfo, 'UNDER', baseDt)
        self.bulkinsertDAL(total_Result, inisType, '2022-08-25')
        return total_Result, metaCdNm




class OptionLoader:
    def __init__(self, batchpath=None, specpath=None):
        self.batchlogManager = BatchlogManager(batchpath, specpath)
        self.stockBatchLog, self.stockCdNm = None, dict()  # 종목 정보
        self.getBatchlog()
        self.optionDTO_list = list(self.optionListDAL())

    def getBatchlog(self):
        opStockTrcd = ['A0184', 'A0034', 'A0025', 'A0134', 'A0174']
        self.stockBatchLog, self.stockCdNm = self.batchlogManager.run(opStockTrcd, 'Option')

    def optionListDAL(self, param=None):
        daoList = db.session.query(OptionDAO).all()
        return daoList

    # 여기는 객체의 정보를 가지고 와서 연산
    def getMaturitylist2(self, insId, callput, atmCd=None, _date=None): # atmcd = O1, I2, A2
        baseDt = _date if _date else datetime.today().strftime("%Y%m%d")
        matList = defaultdict(list)
        var_CP = '42' if callput == 'C' else '43'  # call, put 관리
        var_ATM = 3 if atmCd[0] == 'O' else 2 if atmCd[0] == 'I' else 1   # 0:선물, 1:ATM, 2:ITM, 3:OTM
        for value in self.stockBatchLog.values(): # 데이터를 가져오는 부분에서 객체로 가져와야됨
            if value['기초자산종목코드'] == insId and value['종목코드'][2:4] == var_CP \
                and value['ATM구분코드'] == str(var_ATM) and value['만기일자'] >= baseDt:
                optionDTO = OptionDTO(value)
                matList[value['만기일자']].append(optionDTO)

        # 내부에서는 행사가 기준으로 정렬
        revs = True if atmCd[0] == 'O' else False
        for v in matList.values():
            v.sort(key=lambda x: x.strike, reverse=revs)
        sorted_matList = sorted(matList.items(), key=lambda x: x[0])  # 만기일자, 행사가 기준 정렬
        # [('만기일자', [option1, option2, ... ]), ... ]
        return sorted_matList

    def getMaturitylist(self, insId, postype, atmCd=None, _date=None): # atmcd = O1, I2, A2
        baseDt = _date if _date else datetime.today().strftime("%Y%m%d")
        var_ATM = 3 if atmCd[0] == 'O' else 2 if atmCd[0] == 'I' else 1   # 0:선물, 1:ATM, 2:ITM, 3:OTM
        matList = defaultdict(list)
        for optionDTO in self.optionDTO_list:
            if optionDTO.insId == insId and optionDTO.posType == postype \
                    and optionDTO.atmCd == str(var_ATM) and optionDTO.matDt >= baseDt:
                matList[optionDTO.matDt].append(optionDTO)

        # 내부에서는 행사가 기준으로 정렬
        revs = True if atmCd[0] == 'O' else False
        for v in matList.values():
            v.sort(key=lambda x: x.strike, reverse=revs)
        sorted_matList = sorted(matList.items(), key=lambda x: x[0])  # 만기일자, 행사가 기준 정렬
        # [('만기일자', [option1, option2, ... ]), ... ]
        return sorted_matList



    def stockInfoByOtherInfo(self, insId=None, matidx=None, callput=None, atmCd=None):
        try:
            matList = self.getMaturitylist(insId, callput, atmCd)
            matDt, optionOBJLst = matList[matidx][0], matList[matidx][1]  # 특정 만기에 해당하는 요소
        except:
            print(f"기초자산 \'{insId}\'에 대한 정보가 없습니다.")
            return
        atmIdx = int(atmCd[1:])
        optionObject = optionOBJLst[atmIdx]  # 행사가 순으로 나열된 배열
        return optionObject

    def getOptionListSoredByStrike(self, insId=None, matidx=None, callput=None, atmCd=None):
        try:
            matList = self.getMaturitylist(insId, callput, atmCd)
        except:
            print(f"기초자산 \'{insId}\'에 대한 정보가 없습니다.")
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
        optionDTO = OptionDTO(self.stockBatchLog[inisCd])
        return optionDTO

    # 특정 종목의 반대편 옵션 정보
    def getOpstPosition(self, inisCd):
        try:
            optionObj = self.getStockInfo(inisCd)
        except:
            print(f"종목 \'{inisCd}\'에 대한 정보가 없습니다.")
            return
        for inisCd, value in self.stockBatchLog.items():
            target = OptionDTO(value)
            if target.insId == optionObj.insId and target.posType != optionObj.posType\
                and target.matDt == optionObj.matDt and target.strike == optionObj.strike:
                return OptionDTO(value)


class FutureLoader:
    def __init__(self, batchpath=None, specpath=None):
        self.batchlogManager = BatchlogManager(batchpath, specpath)
        self.stockBatchLog, self.stockCdNm = None, dict()
        self.getBatchlog()

    def getBatchlog(self):
        fuStockTrcd = ['A0014', 'A0164', 'A0015', 'A0124', 'A0094', 'A0104', 'A0024']
        self.stockBatchLog, self.stockCdNm = self.batchlogManager.run(fuStockTrcd, 'Future')

    # 특정 기초자산의 월물에 대한 정보를 담는 곳
    def getMaturitylist(self, insId, _date=None):
        date = _date if _date else datetime.today().strftime("%Y%m%d")
        matList = list()
        for inisCd, value in self.stockBatchLog.items():
            if value['기초자산ID'] == insId and value['만기일자'] > date:
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
        self.stockBatchLog, self.stockCdNm = self.batchlogManager.run(eqStockTrcd, 'Equity')

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

    # spec = MetaData()
    # totalSpecDf, totalSpec = spec.getSpecInfoByDirectory(main_path + '/feed spec')
    # totalTr = spec.getTrInfoByDirectory(main_path + '/feed spec')
    #
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:1234@localhost:3306/MM'
    app.config['SQLALCHEMY_ECHO'] = True
    db.init_app(app)

    with app.app_context(): # Db세션을 연결해야됨
        db.create_all()  # 선언했던 테이블 생성해줘야됨
        daoList = db.session.query(OptionDAO).all()
        optionLoader = OptionLoader(batchpath=feed_file, specpath=feed_spec)
        #futureLoader = FutureLoader(batchpath=feed_file, specpath=feed_spec)
        #equityLoader = EquityLoader(batchpath=feed_file, specpath=feed_spec)
        # option = optionLoader.stockInfoByOtherInfo('K2I', 0, 'C', 'I1')  # 기초자산ID, 월물정보, callput, ATM정보
        # option = optionLoader.stockInfoByOtherInfo('K2I', 1, 'C', 'I1')  # 기초자산ID, 월물정보, callput, ATM정보
        # optionList = optionLoader.getOptionListSoredByStrike('K2I', 0, 'C', 'I')  # 기초자산ID, 월물정보, callput, ATM정보
        #
        # position = optionLoader.getStockInfo('KR4323T30314')  # 포지션
        # opstposition = optionLoader.getOpstPosition('KR4323T30314')  # 반대 포지션
        # # future = futureLoader.stockInfo('KR4101S90005')  # 기초자산ID, 월물정보
        # # equity = equityLoader.stockInfo('HK0000057197')
        # # equity_nm = equityLoader.stockInfo('이스트아시아홀딩스')
        #
        # #print(option.inisCd, option.inisNm)
        # print(optionList)
        # print(position.inisCd, position.inisNm, position.strike)
        # print(opstposition.inisCd, opstposition.inisNm, position.strike)
        # # print(future.inisCd, future.inisNm)
        # # print(equity.inisCd, equity.inisNm)
        # # print(equity_nm.inisCd, equity_nm.inisNm)

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
