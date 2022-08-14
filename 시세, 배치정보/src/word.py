import os
from specInfo import *

# 이 클래스는 항목의 빈도수를 조사하여 전체 정보 중 필요한 정보를 반환하도록 합니다.


class WordToCheck:
    def __init__(self, filepath):
        main_path = 'C:/Users/USER/Downloads/mm/자료/시세, 배치정보'
        filepath = main_path + '/feed spec'
        self.info = MetaData()
        self.TrInfo_df = self.info.getTrInfoByDirectory(filepath)
        self.SpecInfo_df = self.info.getSpecInfoByDirectory(filepath)

    # 이 함수는 특정 단어를 포함하는 SPEC 정보가 가지고 있는 항목들의 최빈값을 계산합니다.
    def commomSpecData(self, df, loc):
        # 특정 칼럼에서 가장 많이 반환된 리스트 생성

        return

    # 이 함수는 특정 단어를 포함하는 TR 목록의 반환 합니다.


if __name__ == "__main__":

    from specInfo import *

    main_path = '..'
    excel = MetaData()

    with pd.ExcelWriter('INFO.xlsx') as writer:
        # SPEC Info
        spec_df = excel.getSpecInfoByDirectory(main_path + '/feed spec')
        spec_df = pd.DataFrame.from_dict(spec_df, orient='index')
        spec_df.to_excel(writer, sheet_name='SPEC정보')
        # TR Info
        tr_df = excel.getTrInfoByDirectory(main_path + '/feed spec')
        tr_df = pd.DataFrame.from_dict(tr_df, orient='index')
        tr_df.to_excel(writer, sheet_name='TR목록')


