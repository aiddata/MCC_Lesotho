

import rasterio
from rasterio.plot import show


fpath = r"/home/mirandalv/Documents/github/MCC_Lesotho/dataset/WaterMasks_SWI_ThresholdsOut_2018_2021.tif"

#20201019, 20200713,20200601, 20200323, 20200210, 20191230, 20191104, 20190520, 20190408, 20190211

timelist = ['20181217', '20181231', '20190114', '20190211', '20190225', '20190408', '20190422', '20190506',
            '20190520', '20190603', '20190701', '20190715', '20190812', '20190826', '20190909', '20190923',
            '20191007', '20191021', '20191104', '20191118', '20191230', '20200113', '20200127', '20200210',
            '20200224', '20200323', '20200420', '20200504', '20200518', '20200601', '20200615','20200629',
            '20200713', '20200727', '20200810', '20200824', '20200907', '20200921', '20201005','20201019',
            '20201102', '20201116', '20201130', '20210208', '20210222', '20210308', '20210322','20210405',
            '20210503', '20210517', '20210531']

src = rasterio.open(fpath)
bd_count = src.count
profile = src.profile

for i in range(1,bd_count+1):

    profile.update(
        count=1)

    img_array = src.read(i)

    nm = 'WaterMasks_SWI_ThresholdsOut_%s.tif'%(timelist[i-1])

    with rasterio.open(nm, 'w', **profile) as dst:
        dst.write(img_array,1)


