import pandas as pd
from collections import deque

class ExcelByPandas:
    def __init__(self):
        self.totalTrInfo = dict()
        self.totalSpecInfo = dict()

    def getTrInfo(self, filepath):
        tr_df = pd.read_excel(filepath, sheet_name='TR목록', usecols='B,C,E', names=['TR명','DATA구분','Size'])
        tr_df['파일명'] = filepath
        tr_df = tr_df[tr_df['TR명'] != 'TR명']
        tr_df = tr_df.dropna(axis=0)
        trInfo = tr_df.set_index('DATA구분').T.to_dict()
        return trInfo

    # 특정 디렉토리 밑의 여러 파일의 전체 TR 목록
    def getTotalTrInfo(self, workspace):
        for file in os.listdir(workspace):
            filepath = os.path.join(workspace, file)
            trInfo = self.getTrInfo(filepath)
            self.totalTrInfo.update(trInfo)
        return self.totalTrInfo

    # 특정 파일에 있는 SPEC 정보
    def getSpecInfoByfile(self, filepath):
        specInfo = pd.read_excel(filepath, sheet_name='SPEC상세', usecols='B,D')
        # 결측치를 제거하는 부분
        specInfo = specInfo.dropna(axis=0) 
        specInfo = specInfo[(specInfo['Unnamed: 1'] != 'TR명') & (specInfo['Unnamed: 1'] != '항목명')]  # 각각의 인덱스를 구하고 지우기
        specIndex = specInfo[(specInfo['Unnamed: 3'].str.isdigit() == False)]
        specInfo_dict = {}
        Q = deque(specIndex.index)
        start = Q.popleft()
        while Q:
            end = Q.popleft()
            title = specIndex.loc[start, 'Unnamed: 1']
            specInfo_dict[title] = specInfo.loc[start+1:end-1, :].values.tolist()
            start = end
        return specInfo_dict

    def getTotalSpecInfo(self, workspace):
        for file in os.listdir(workspace):
            filepath = os.path.join(workspace, file)
            specInfo_dict = self.getSpecInfoByfile(filepath)
            self.totalSpecInfo.update(specInfo_dict)
        return self.totalSpecInfo

    # 특정 TR의 SPEC 정보
    def getSpecInfoByTRName(self, trname):
        # 항목명과 길이를 매핑
        trSpecInfo = self.totalSpecInfo[trname]  # 엑셀파일에 있는 spec의 정보들 중에서 관련 TR의 내용만 가져오기
        # TR이름을 만족하는 인덱스를 구해서 범위만큼 슬라이싱하기
        return trSpecInfo

if __name__ == "__main__":
    # 경로 설정
    import os
    main_path = 'C:/Users/USER/Downloads/mm/자료/시세, 배치정보'
    feed_spec = os.path.join(main_path, "feed spec/KOSPI200지수옵션_실시간_UDP(12M)_1.550_2022080301.xls")

    # Get SPEC Info
    excel = ExcelByPandas()
    print(excel.getTrInfo(feed_spec))
    print(excel.getTotalTrInfo(main_path + '/feed spec'))
    #print(excel.getSpecInfoByfile(feed_spec))
    #excel.getTotalSpecInfo(main_path + '/feed spec')
    print(excel.totalSpecInfo,end="")