
class UnderlyingDTO:
    def __init__(self, rawData):
        self.rawData = rawData
        self.insId = None
        self.insNm = None
        self.insPrice = None
        self.baseDt = None
        self.mapDataWithfield()

    def getMetaInfo(self):
        # dictionay에 매핑된 정보와 변수를 매핑한다 ('한글로 된 정보': 변수명')
        metaData = {'기초자산ID': "insId",
                    #'기초자산명': "insNm",
                    '기초자산종가': "insPrice",
                    '영업일자(입회일자)': 'baseDt',
                    }
        return metaData

    def mapDataWithfield(self):
        metaData = self.getMetaInfo()
        for key, value in metaData.items():
            if 'price' in value.lower():
                exec(f'self.{value} = \'{self.formatting2(self.rawData[key])}\'')
            else:
                exec(f'self.{value} = \'{self.rawData[key]}\'')

       # self.insNm = self.getInsNm(self.insId)

    def formatting2(self, num):
        return '{:,.2f}'.format(float(int(num)/100))

    def getInsNm(self, insId):
        import pandas as pd
        filepath = 'C:/Users/USER/Downloads/mm/자료/기타/기초자산ID.csv'
        tr_df = pd.read_csv(filepath, encoding='EUC-KR')
        return tr_df




class OptionDTO:
    def __init__(self, rawData):
        self.rawData = rawData
        self.inisType = 'Option'
        self.inisCd = None
        self.inisNm = None
        self.insId = None
        self.matDt = None
        self.baseDt = None
        self.atmCd = None
        self.strike = None
        self.price = None
        self.upPrice1 = None
        self.upPrice2 = None
        self.upPrice3 = None
        self.lowPrice1 = None
        self.lowPrice2 = None
        self.lowPrice3 = None
        self.prevTransAmt = None
        self.prevTransPrc = None
        self.posType = None  # 따로 계산
        self.mapDataWithfield()

    def metaInfoManager(self):  # metaData를 관리하는 곳
        metaData = {'종목코드': "inisCd",
                    '종목한글명': "inisNm",
                    '기초자산ID': 'insId',
                    '만기일자': 'matDt',
                    '영업일자(입회일자)': 'baseDt',
                    'ATM구분코드': 'atmCd',
                    '행사가격': 'strike',
                    '기준가': 'price',
                    '가격제한1단계상한가': 'upPrice1',
                    "가격제한2단계상한가": "upPrice2",
                    "가격제한3단계상한가": "upPrice3",
                    "가격제한1단계하한가": "lowPrice1",
                    "가격제한2단계하한가": "lowPrice2",
                    "가격제한3단계하한가": "lowPrice3",
                    '전일체결수량': 'prevTransAmt',
                    '전일거래대금': 'prevTransPrc',
                    }
        return metaData

    # 메타정보에 맞춰 rawData와 변수를 매핑해주는 곳
    def mapDataWithfield(self):
        metaData = self.metaInfoManager()
        for key, value in metaData.items():
            if 'price' in value.lower():
                exec(f'self.{value} = \'{self.formatting2(self.rawData[key])}\'')
            elif 'strike' == value:
                exec(f'self.{value} = \'{self.formatting8(self.rawData[key])}\'')
            else:
                exec(f'self.{value} = \'{self.rawData[key]}\'')

        self.posType = 'Call' if self.inisCd and self.inisCd[2:4] == '42' else 'Put'  # call, put 관리
        self.atmCd = 'OTM' if self.atmCd == '3' else 'ITM' if self.atmCd == '2' else 'ATM'  # 0:선물, 1:ATM, 2:ITM, 3:OTM


    def formatting8(self, num):
        return '{:,.8f}'.format(float(int(num)/100000000))

    def formatting2(self, num):
        return '{:,.2f}'.format(float(int(num)/100))



class FutureDTO:
    def __init__(self, rawData):
        self.rawData = rawData
        self.inisType = 'Future'
        self.inisCd = None
        self.inisNm = None
        self.insId = None
        self.matDt = None
        self.baseDt = None
        self.strike = None
        self.price = None
        self.upPrice1 = None
        self.upPrice2 = None
        self.upPrice3 = None
        self.lowPrice1 = None
        self.lowPrice2 = None
        self.lowPrice3 = None
        self.prevTransAmt = None
        self.prevTransPrc = None
        self.mapDataWithfield()

    def metaInfoManager(self):
        metaData = {'종목코드': "inisCd",
                    '종목한글명': "inisNm",
                    '기초자산ID': 'insId',
                    '만기일자': 'matDt',
                    '영업일자(입회일자)': 'baseDt',
                    '행사가격': 'strike',
                    '기준가': 'price',
                    '가격제한1단계상한가': 'upPrice1',
                    "가격제한2단계상한가": "upPrice2",
                    "가격제한3단계상한가": "upPrice3",
                    "가격제한1단계하한가": "lowPrice1",
                    "가격제한2단계하한가": "lowPrice2",
                    "가격제한3단계하한가": "lowPrice3",
                    '전일체결수량': 'prevTransAmt',
                    '전일거래대금': 'prevTransPrc',
                    }

        return metaData

    def mapDataWithfield(self):
        metaData = self.metaInfoManager()
        for key, value in metaData.items():
            if 'price' in value.lower():
                exec(f'self.{value} = \'{self.formatting2(self.rawData[key])}\'')
            elif 'strike' == value:
                exec(f'self.{value} = \'{self.formatting8(self.rawData[key])}\'')
            else:
                exec(f'self.{value} = \'{self.rawData[key]}\'')

    def formatting8(self, num):
        return '{:,.8f}'.format(float(int(num)/100000000))

    def formatting2(self, num):
        return '{:,.2f}'.format(float(int(num)/100))


class EquityDTO:
    def __init__(self, rawData):
        self.rawData = rawData
        self.inisType = 'Equity'
        self.inisCd = None
        self.inisNm = None
        self.matDt = None
        self.baseDt = None
        self.price = None
        self.upPrice = None
        self.lowPrice = None
        self.groupId = None  # 증권그룹ID
        self.prevTransAmt = None
        self.prevTransPrc = None
        self.mapDataWithfield()

    def metaInfoManager(self):
        # dictionay에 매핑된 정보와 변수를 매핑한다 ('한글로 된 정보': 변수명')
        metaData = {'종목코드': "inisCd",
                    '종목한글약명': "inisNm",
                    '만기일자': 'matDt',
                    '영업일자': 'baseDt',
                    '기준가격': 'price',
                    '상한가': 'upPrice',
                    '하한가': 'lowPrice',
                    '증권그룹ID': 'groupId',  # 증권그룹ID
                    '전일누적체결수량': 'prevTransAmt',
                    '전일누적거래대금': 'prevTransPrc',
                    }
        return metaData

    def mapDataWithfield(self):
        metaData = self.metaInfoManager()
        for key, value in metaData.items():
            if 'price' in value.lower():
                exec(f'self.{value} = \'{self.formatting2(self.rawData[key])}\'')
            else:
                exec(f'self.{value} = \'{self.rawData[key]}\'')

    def formatting8(self, num):
        return '{:,.8f}'.format(float(int(num)/100000000))

    def formatting2(self, num):
        return '{:,.2f}'.format(float(int(num)/100))


if __name__ == "__main__":
    underlying = UnderlyingDTO(dict())
    underlying.getInsNm('sdf')
