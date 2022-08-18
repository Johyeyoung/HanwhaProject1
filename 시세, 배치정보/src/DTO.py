class OptionDTO:
    def __init__(self, rawData):
        self.rawData = rawData
        self.inisType = 'OP'
        self.inisCd = None
        self.inisNm = None
        self.insCd = None
        self.matDt = None
        self.atmCd = None
        self.strike = None
        self.posType = None  # 따로 계산
        self.status = None   # 따로 계산
        self.baseDt = None
        self.mapDataWithfield()

    def metaInfoManager(self):  # metaData를 관리하는 곳
        metaData = {'종목코드': "inisCd",
                    '종목한글명': "inisNm",
                    '기초자산종목코드': 'insCd',
                    '만기일자': 'matDt',
                    'ATM구분코드': 'atmCd',
                    '행사가격': 'strike',
                    '영업일자(입회일자)': 'baseDt'}
        return metaData

    # 메타정보에 맞춰 rawData와 변수를 매핑해주는 곳
    def mapDataWithfield(self):
        metaData = self.metaInfoManager()
        for key, value in metaData.items():
            exec(f'self.{value} = \'{self.rawData[key]}\'')

        self.posType = 'C' if self.inisCd and self.inisCd[2:4] == '42' else '43'  # call, put 관리
        if self.strike: self.strike = '{:,.8f}'.format(float(int(self.strike)/100000000))


class FutureDTO:
    def __init__(self, rawData):
        self.rawData = rawData
        self.inisType = 'FU'
        self.inisCd = None
        self.inisNm = None
        self.insCd = None
        self.matDt = None
        self.baseDt = None
        self.mapDataWithfield()

    def getMetaInfo(self):
        metaData = {'종목코드': "inisCd",
                    '종목한글명': "inisNm",
                    '기초자산종목코드': 'insCd',
                    '만기일자': 'matDt',
                    '영업일자(입회일자)': 'baseDt'}

        return metaData

    def mapDataWithfield(self):
        metaData = self.getMetaInfo()
        for key, value in metaData.items():
            exec(f'self.{value} = \'{self.rawData[key]}\'')


class EquityDTO:
    def __init__(self, rawData):
        self.rawData = rawData
        self.inisType = 'EQ'
        self.inisCd = None
        self.inisNm = None
        self.baseDt = None
        self.mapDataWithfield()

    def getMetaInfo(self):
        # dictionay에 매핑된 정보와 변수를 매핑한다 ('한글로 된 정보': 변수명')
        metaData = {'종목코드': "inisCd",
                    '종목한글약명': "inisNm",
                    '영업일자(입회일자)': 'baseDt'}
        return metaData

    def mapDataWithfield(self):
        metaData = self.getMetaInfo()
        for key, value in metaData.items():
            exec(f'self.{value} = \'{self.rawData[key]}\'')

