import pandas as pd
from collections import deque
import os
import re

class MetaData:
    def __init__(self, filepath=None):
        self.totalTrDf = None
        self.totalTrDict = dict()
        self.totalSpecDf = None
        self.totalSpecDict = dict()

    def setPath(self, filepath):
        pass

    # 이 함수는 특정 파일에 존재하는 모든 TR 목록을 가져 옵니다.
    def getTrInfoByFile(self, filepath=None):
        try:
            tr_df = pd.read_excel(filepath, sheet_name='TR목록', usecols='B,C,E', names=['TR명','DATA구분','Size'])
            tr_df['파일명'] = filepath
            tr_df = tr_df[tr_df['TR명'] != 'TR명'].dropna(axis=0)
            return tr_df

        except Exception as e:
            print(e)

    # 이 함수는 특정 디렉토리 밑의 여러 파일의 전체 TR 목록을 가져 옵니다.
    def getTrInfoByDirectory(self, directory):
        try:
            for file in os.listdir(directory):
                filepath = os.path.join(directory, file)
                tr_df = self.getTrInfoByFile(filepath)
                self.totalTrDf = pd.concat([self.totalTrDf, tr_df])
            self.totalTrDict = self.totalTrDf.set_index('DATA구분').T.to_dict()  # 딕셔너리 타입 저장
            return self.totalTrDf

        except Exception as e:
            print(e)

    # 이 함수는 특정 파일에 존재하는 모든 SPEC 정보를 가져 옵니다.
    def getSpecInfoByFile(self, filepath=None):
        specInfo = pd.read_excel(filepath, sheet_name='SPEC상세', usecols='B,D', names=['항목명', '길이'])
        # 결측치를 제거하는 부분
        specInfo = specInfo.dropna(axis=0)
        specInfo = specInfo[(specInfo['항목명'] != 'TR명') & (specInfo['항목명'] != '항목명')]  # 각각의 인덱스를 구하고 지우기
        specIndex = specInfo[(specInfo['길이'].str.isdigit() == False)]
        Q = deque(specIndex.index)
        start = Q.popleft()
        spec_df, spec_dict = None, dict()
        while Q:
            end = Q.popleft()
            title = specIndex.loc[start, '항목명']
            subdf = specInfo.loc[start+1:end-1, :]
            # dictionay 용
            spec_dict[title] = subdf.values.tolist()
            # dataframe 용
            subdf.insert(loc=0, column='TR명', value=title)
            spec_df = pd.concat([spec_df, subdf])
            start = end
        return spec_df, spec_dict

    # 이 함수는 특정 폴더 밑에 존재하는 모든 파일의 SPEC 정보를 가져 옵니다.
    def getSpecInfoByDirectory(self, directory):
        try:
            for file in os.listdir(directory):
                filepath = os.path.join(directory, file)
                specDf, specDict = self.getSpecInfoByFile(filepath)
                self.totalSpecDict.update(specDict)
                self.totalSpecDf = pd.concat([self.totalSpecDf, specDf])
            return self.totalSpecDf, self.totalSpecDict
        except Exception as e:
            print(e)

    # 이 함수는 특정 TR에 해당하는 SPEC 정보를 가져 옵니다.
    def getSpecInfoByTrNm(self, trNm):
        trSpecInfo = self.totalSpecDict[trNm]
        return trNm, trSpecInfo

    # 이 함수는 특정 word를 포함하고 있는 SPEC 정보를 가져 옵니다.
    def getSpecInfoBySubstr(self, substr, df=None):
        df = df if isinstance(df, pd.DataFrame) else self.totalSpecDf
        substr = [f'(?=.*{_str}+)' for _str in substr.split(',')]
        condition = r''.join(substr) + r'.*'

        targetSpecDf = df[df['TR명'].str.contains(condition, regex=True)]
        targetSpecDict = dict()

        for key, value in self.totalSpecDict.items():
            if re.compile(condition).search(key):
                targetSpecDict[key] = value

        return targetSpecDf, targetSpecDict

if __name__ == "__main__":
    # 경로 설정
    import os
    main_path = 'C:/Users/USER/Downloads/mm/자료/시세, 배치정보'
    feed_spec = os.path.join(main_path, "feed spec/KOSPI200지수옵션_실시간_UDP(12M)_1.550_2022080301.xls")

    # Get SPEC Info
    specdata = MetaData()
    #print(specdata.getTrInfoByFile(feed_spec))
    #print(specdata.getTrInfoByDirectory(main_path + '/feed spec'))

    #print(specdata.getSpecInfoByFile(feed_spec))
    specdata.getSpecInfoByDirectory(main_path + '/feed spec')

    #print(specdata.getSpecInfoByTRName('K200옵션_경쟁+협의합산'))

    saveDict = dict()

    futureDf, futureDict = specdata.getSpecInfoBySubstr('선물')
    optionDf, optionDict = specdata.getSpecInfoBySubstr('옵션')
    equityDf, equityDict = specdata.getSpecInfoBySubstr('현물')
    '''
        saveDict['선물_TR명'] = futureDict.keys()
        saveDict['옵션_TR명'] = optionDict.keys()
        saveDict['현물_TR명'] = equityDict.keys()
    '''


    saveDict['선물_항목명'] = futureDf.value_counts(subset=['항목명'])
    saveDict['옵션_항목명'] = optionDf.value_counts(subset=['항목명'])
    saveDict['현물_항목명'] = equityDf.value_counts(subset=['항목명'])
    saveDict['현선물_항목명'] = equityDf.value_counts(subset=['항목명'])

    # 엑셀에 데이터 저장하기
    with pd.ExcelWriter('Result.xlsx') as writer:
        for key, value in saveDict.items():
            value.to_excel(writer, sheet_name=key)

    from collections import defaultdict
    key_list = defaultdict(int)
    for key in specdata.totalSpecDict.keys():
        keys = key.replace('_', ' ')
        cut = ''
    #   if '주식' in keys: cut = '주식'
    #   elif '선물' in keys: cut = '선물'
    #   elif '옵션' in keys: cut = '옵션'
        try:
            check = keys.split(cut)
            key_list[check[1].strip()] += 1
            # print(keys, check)
        except:
            print(key)
            continue

    print(key_list)

    key_list = list()
    for key in specdata.totalSpecDict.keys():
        keys = key.replace('_', ' ')
        if '종목배치' in keys:
            key_list.append(keys)


    print(key_list)
