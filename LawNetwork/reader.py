import requests

with open('titles.txt') as f:
    titles = f.readlines()
    # Some titles are substrings of other titles
    # E.g. OBRA and COBRA (two different acts)
    # Naive substring search would catch cobra when searching for obra
    # Sort titles by length (descending)
    # And remove them after they've been found
    stitles = sorted(titles, key=len)
    stitles.reverse()

with open('Dates.txt') as g:
  dates = g.readlines()
    
def findTitles(billtext):
  # Text cleanup
  billtext = billtext.replace('\n','')
  billtext = ' '.join(billtext.split())

  out = []
  for t in stitles:
    t = t[:-1]
    if (t in billtext):
      out.append(t)
      # Remove all instances so substrings are not found
      billtext = billtext.replace(t, '')
  
  for d in dates:
    d = d[:-1]
    if ('Act of '+d in billtext):
      out.append('Act of '+d)
  
  return out

# Govinfo law numbers
SALnums = [802, 15290, 1837, 13736, 16738, 16716, 10844, 5328, 13738, 10297, 11540, 5330, 8932, 5353, 5331, 10313, 5333, 9517, 1332, 10240, 10285, 1, 10210, 5282, 5108, 10251, 15088, 10252, 10212, 5336, 10239, 13727, 11575, 13875, 212, 2987, 12611, 11362, 12009, 16718, 9607, 15703, 13769, 3126, 10422, 14954, 11724, 16367, 12190, 16211, 15579, 8161, 16551, 13879, 1334, 2998, 13998, 725, 1528, 1529, 11591, 11645, 10241, 10242, 10214, 10245, 10872, 10254, 10316, 10255, 10310, 12449, 10257, 10258, 10260, 10259, 1105, 10286, 10288, 10299, 10261, 10327, 15214, 11740, 10235, 10217, 916, 1166, 10997, 12453, 11604, 13909, 13805, 15475, 15716, 10653, 10415, 9539, 9611, 9614, 9821, 11739, 12001, 15278, 913, 10925, 209, 10354, 10703, 859, 860, 15506, 16380, 11725, 11310, 13877, 10702, 14968, 11091, 15286, 13996, 16028, 247, 12220, 9970, 11490, 15473, 10075, 10945, 10713, 5293, 1397, 767, 12678, 13630, 12043, 9276, 16472, 11423, 3074, 14003, 10390, 1838, 803, 15833, 10041, 1795, 1656, 2957, 966, 15549, 10524, 10262, 1839, 1657, 1840, 382, 12617, 10594, 5312, 15559, 11713, 213, 15827, 15302, 12640, 1629, 9765, 1707, 10651, 1708, 1059, 1061, 242, 882, 9309, 884, 15255, 15340, 13781, 1335, 2999, 11075, 11866, 8318, 15772, 1658, 1659, 1660, 1661, 1630, 10410, 451, 450, 11065, 15481, 383, 914, 915, 13664, 13755, 15784, 12202, 3066, 16284, 10708, 10709, 249, 10658, 251, 252, 253, 254, 1106, 255, 16365, 10119, 10992, 10263, 9727, 9805, 15561, 10247, 11354, 10034, 11792, 15234, 10685, 11720, 14173, 15500, 11629, 10552, 11021, 13821, 15496, 1062, 1063, 13745, 15259, 3108, 10536, 11726, 11551, 9896, 16487, 9772, 11615, 13729, 12013, 11766, 10334, 5283, 10474, 5324, 10079, 460, 12161, 15689, 11300, 9566, 16217, 15616, 12037, 1037, 10544, 9318, 11564, 10652, 1107, 931, 10416, 16730, 9855, 15754, 2958, 15541, 15905, 3096, 15455, 13929, 15253, 11651, 1435, 1436, 1437, 1438, 15662, 1663, 12152, 15774, 215, 256, 14598, 11554, 15896, 805, 806, 807, 9619, 11302, 16015, 10503, 11810, 10328, 10067, 934, 10894, 1364, 15310, 16489, 15512, 1339, 5139, 9924, 16351, 15693, 12472, 340, 341, 342, 343, 15352, 345, 346, 347, 9775, 13809, 12206, 5110, 5109, 1439, 819, 11566, 3049, 877, 878, 11478, 2989, 11318, 10175, 12155, 10429, 10081, 14171, 9541, 10592, 12457, 15405, 1664, 10647, 1666, 10978, 16585, 15423, 11002, 15620, 16029, 16485, 9617, 15354, 13840, 16121, 462, 15646, 1841, 15758, 10215, 10329, 10309, 936, 937, 938, 257, 10701, 258, 16189, 11993, 10289, 9609, 12178, 11122, 9362, 967, 10501, 10426, 15356, 16571, 15574, 8321, 15330, 808, 10620, 15030, 10356, 16530, 13868, 1796, 16546, 11549, 10406, 9776, 12454, 15486, 10243, 10216, 10502, 11589, 16454, 260, 384, 9748, 9618, 12226, 13724, 15557, 15502, 13881, 10018, 11079, 995, 11248, 10355, 932, 14561, 10892, 1108, 10823, 15999, 11600, 8937, 15675, 11360, 15218, 13896, 13726, 10095, 15251, 16281, 16378, 11425, 13732, 16019, 10290, 12636, 10591, 5291, 11501, 1842, 15296, 12455, 15328, 10113, 10264, 12601, 11411, 16470, 11115, 15626, 16361, 1561, 2973, 10626, 12033, 15318, 15800, 10715, 467, 10716, 471, 10409, 8323, 476, 10600, 5159, 10211, 10209, 5310, 10342, 5097, 9551, 10307, 1442, 477, 478, 1444, 1445, 1446, 479, 10403, 8040, 8041, 11978, 480, 482, 483, 10454, 488, 1483, 10622, 726, 15272, 849, 5317, 3125, 10585, 9542, 11570, 13982, 15570, 12017, 11613, 10351, 10828, 11125, 11124, 10635, 12676, 13832, 10400, 3102, 10660, 5370, 15417, 13638, 15753, 12149, 10608, 11101, 11736, 12192, 13749, 15280, 15504, 16534, 14269, 15875, 9219, 10993, 10830, 10834, 16213, 489, 1767, 1768, 10089, 15650, 11658, 11465, 16030, 13632, 11714, 10937, 15911, 10393, 3001, 11830, 13731, 9779, 10506, 13751, 11023, 10513, 14569, 11814, 708, 709, 10470, 9992, 15528, 10664, 9515, 9858, 712, 14287, 13803, 1668, 11649, 13423, 16017, 1769, 971, 10691, 10186, 15802, 3114, 11324, 10610, 11447, 13767, 1843, 9920, 14283, 16197, 10831, 15539, 14564, 11127, 727, 763, 745, 10448, 3093, 809, 747, 15737, 12658, 15433, 16203, 10266, 13968, 13765, 11861, 940, 748, 730, 731, 15362, 12194, 15282, 15640, 15904, 15735, 13687, 10345, 8925, 840, 10330, 5174, 11776, 5396, 10267, 10213, 15086, 15453, 11111, 894, 1797, 16479, 16460, 5287, 8095, 16376, 15381, 2962, 2963, 2964, 12456, 12660, 896, 1530, 15835, 16742, 10173, 15239, 3002, 832, 15555, 1631, 841, 10420, 8929, 8931, 10914, 845, 1634, 10425, 866, 12452, 3121, 13834, 11731, 12664, 16559, 12007, 10301, 10337, 13870, 11443, 11758, 11847, 15614, 11863, 900, 1760, 10048, 11851, 11999, 11097, 10571, 12158, 3085, 10302, 10268, 3057, 12157, 1348, 1069, 1349, 9887, 16375, 15893, 15778, 9829, 16001, 13757, 10218, 1514, 1515, 385, 15387, 10700, 12039, 9799, 15630, 15683, 1832, 15457, 1770, 811, 10314, 10236, 10269, 10505, 16373, 13001, 10002, 1008, 15413, 1009, 13999, 13793, 10234, 917, 12646, 918, 221, 1845, 1846, 12216, 919, 16505, 386, 1717, 972, 942, 9766, 264, 10238, 10265, 265, 11445, 985, 1806, 854, 1847, 1038, 973, 10827, 387, 268, 10353, 11802, 10326, 10383, 1718, 1719, 11662, 10402, 12077, 12644, 1592, 15407, 10270, 1521, 855, 1563, 10581, 11800, 15226, 834, 1010, 12672, 13940, 10417, 269, 270, 9834, 5115, 5117, 10253, 1597, 10445, 388, 389, 296, 11729, 2974, 1447, 1419, 1420, 2966, 1398, 13797, 12103, 975, 10913, 11864, 13747, 15187, 10644, 10131, 13936, 9519, 13728, 3003, 15490, 12154, 1670, 13799, 3091, 390, 15205, 9543, 10920, 10919, 10921, 10918, 10916, 10922, 10917, 1117, 10567, 1039, 12089, 13636, 10219, 10220, 9932, 10331, 10303, 10250, 10649, 10237, 11467, 12003, 1448, 12107, 10171, 1071, 10249, 9569, 12652, 1449, 10633, 1351, 10453, 10580, 10654, 1076, 1451, 1077, 1540, 5394, 1119, 1120, 1121, 14607, 13207, 15344, 9928, 11552, 10161, 10548, 14296, 9771, 15605, 15167, 12085, 13003, 13777, 15350, 507, 10271, 10522, 15817, 1531, 3004, 14602, 15891, 9608, 11764, 12591, 13828, 15520, 15877, 9521, 16031, 16557, 11553, 10886, 5320, 13681, 12597, 10123, 16503, 15222, 13883, 920, 732, 1565, 15247, 1352, 12099, 14289, 15342, 13654, 16133, 10707, 10970, 12476, 11732, 11812, 10004, 14596, 11306, 272, 11469, 11980, 15624, 11762, 15748, 16005, 2990, 1672, 10896, 15865, 15565, 10062, 11109, 812, 9979, 16477, 14258, 10982, 15346, 764, 13691, 10115, 10292, 16540, 15459, 1399, 10006, 15997, 10576, 11556, 10405, 1772, 1773, 1774, 1123, 10332, 792, 10579, 10614, 14251, 10483, 9939, 10550, 16127, 15518, 10706, 11000, 1848, 765, 766, 10659, 770, 9467, 11069, 1421, 11025, 976, 16583, 10687, 11794, 15292, 5322, 15889, 16517, 5381, 10878, 273, 11132, 1143, 10876, 1206, 15739, 15534, 11352, 9980, 9774, 10059, 15235, 5178, 10349, 5181, 10344, 5186, 10835, 5191, 10596, 8941, 5232, 5248, 5249, 12180, 11539, 10451, 5250, 5251, 772, 773, 11043, 10272, 13753, 11660, 10542, 1827, 11031, 15815, 15977, 11476, 13223, 13677, 1374, 1375, 1376, 1377, 1378, 10559, 11121, 15871, 977, 11790, 14320, 753, 11760, 14175, 15873, 11055, 10577, 298, 299, 301, 5252, 10504, 1401, 1402, 16115, 13810, 13830, 1404, 1405, 5297, 1406, 5296, 5299, 10401, 12083, 755, 15837, 15334, 1012, 12670, 10995, 12628, 9935, 11859, 1453, 1454, 1455, 10427, 1457, 1458, 1459, 1460, 1461, 1462, 1463, 1464, 1465, 1466, 1467, 1468, 1469, 1470, 1471, 1472, 1473, 9630, 9631, 9632, 9813, 10398, 10986, 1474, 1475, 1476, 1477, 10655, 8188, 15809, 10192, 13864, 1676, 1422, 14560, 923, 3117, 225, 275, 302, 10590, 11577, 1079, 1356, 10447, 5253, 11857, 11578, 1078, 10452, 11576, 15863, 10198, 1878, 1879, 11596, 9189, 10010, 15298, 15224, 16569, 10182, 1081, 13785, 12668, 1587, 16215, 13858, 12143, 303, 9904, 14185, 15483, 10387, 15257, 11818, 16205, 10481, 16388, 3006, 12224, 10663, 14956, 14298, 825, 15411, 16542, 13942, 9757, 10153, 13931, 3115, 13994, 789, 10943, 15009, 14304, 5111, 12230, 14254, 9975, 8190, 1511, 5401, 1677, 11041, 11666, 10137, 11653, 1849, 10648, 10419, 13866, 15718, 1286, 9616, 16032, 15393, 305, 3107, 9317, 1761, 11541, 15825, 3072, 1533, 11708, 12147, 10181, 16185, 14001, 11741, 10030, 13874, 5130, 902, 226, 1522, 10645, 1635, 10032, 1720, 10586, 5368, 15304, 1678, 1014, 15720, 16458, 12133, 10073, 10338, 1679, 1680, 10389, 1880, 15563, 13848, 16153, 5335, 11441, 12153, 10570, 15367, 15425, 1776, 11661, 11128, 11637, 10391, 11833, 10650, 1777, 5323, 1543, 15679, 11976, 887, 15805, 15210, 1851, 11806, 13851, 1516, 3007, 5403, 3009, 10036, 522, 10322, 527, 13661, 1798, 8336, 1566, 1567, 1568, 5337, 10026, 978, 10606, 10574, 1381, 15288, 16011, 5356, 12992, 15336, 11063, 10966, 10642, 5385, 13862, 10008, 10165, 10046, 10705, 5256, 5255, 15736, 11081, 5329, 1125, 243, 15415, 1082, 15216, 979, 15193, 10604, 1852, 1853, 10434, 1854, 1855, 10589, 1859, 10822, 12680, 10248, 10246, 1628, 10293, 278, 279, 9942, 12021, 10833, 12610, 1603, 13783, 10560, 228, 229, 2975, 10826, 10714, 10411, 10407, 10388, 10386, 11477, 10045, 10359, 11141, 11977, 11831, 13740, 13932, 10572, 10634, 10656, 634, 15300, 10385, 10424, 814, 10352, 14604, 3010, 11555, 15189, 15007, 15377, 14310, 1126, 1127, 9570, 12478, 244, 1604, 9767, 11772, 15461, 1425, 3064, 12666, 10343, 10712, 5388, 14170, 1779, 14255, 10864, 8189, 16363, 14250, 15098, 10382, 10930, 13974, 3128, 638, 307, 10423, 13694, 639, 15979, 1684, 1724, 1725, 5373, 1726, 1129, 1128, 15516, 12011, 16033, 15322, 1865, 10350, 1867, 1685, 16034, 1493, 1494, 1869, 15547, 733, 1870, 1871, 1727, 925, 5240, 1300, 12662, 308, 14252, 3011, 12184, 13905, 12049, 1409, 11130, 1301, 11136, 10347, 10837, 1411, 868, 869, 775, 13674, 870, 11073, 11647, 15867, 1302, 15983, 5113, 10287, 9198, 12196, 15714, 15391, 11737, 10467, 11407, 230, 16561, 15308, 16554, 1382, 13730, 1728, 15899, 10507, 15245, 13846, 11457, 12480, 10091, 888, 2976, 5386, 15578, 15723, 3012, 11033, 11985, 10196, 12602, 10968, 13656, 15429, 1687, 15782, 11643, 348, 15360, 1636, 1523, 11574, 1026, 11832, 2991, 10037, 827, 828, 829, 12005, 13206, 9316, 10221, 1569, 5261, 1696, 15087, 1639, 10832, 10232, 15530, 16007, 10852, 16023, 14960, 1142, 16219, 10616, 980, 12585, 857, 12648, 835, 1689, 10273, 15526, 15628, 16743, 10934, 15494, 10510, 3101, 11027, 10994, 10077, 16171, 11808, 9307, 15284, 10058, 11083, 16475, 10612, 15727, 15710, 1083, 5104, 16175, 1731, 1881, 12448, 14318, 10693, 10274, 11405, 440, 446, 441, 1793, 10022, 15488, 871, 10882, 11475, 10139, 5387, 9818, 12081, 15636, 3013, 13907, 10317, 10275, 10276, 13825, 14000, 10848, 392, 12113, 1517, 13222, 11721, 10208, 10277, 10598, 15551, 13779, 872, 16283, 15829, 16163, 15306, 14253, 15642, 11304, 9977, 11599, 1612, 15658, 15312, 11117, 1613, 1782, 12101, 15831, 12650, 12626, 1027, 873, 11455, 9275, 12031, 16207, 13787, 10397, 11503, 15104, 11734, 15435, 15660, 14259, 15807, 16117, 15364, 16720, 16587, 15746, 11756, 13789, 15276, 13986, 1783, 10932, 10933, 312, 313, 314, 5314, 8771, 8772, 8773, 8774, 8776, 10584, 8778, 8779, 8775, 8780, 8781, 8782, 8783, 8784, 8786, 8787, 8788, 8789, 8785, 8790, 8791, 8792, 8793, 8794, 8796, 8797, 8798, 8799, 8795, 9279, 9280, 10057, 9473, 10125, 10203, 1130, 15819, 15823, 16354, 16369, 10205, 10229, 13628, 954, 838, 331, 15326, 11089, 11722, 707, 1087, 1800, 1824, 1801, 1825, 10468, 13652, 15199, 11816, 1317, 15100, 5343, 15532, 15522, 15212, 10509, 1620, 15707, 13938, 15371, 12087, 14169, 5363, 10514, 1621, 758, 1802, 799, 15821, 10984, 16728, 9629, 13925, 1134, 9994, 9860, 15681, 16055, 10294, 5406, 285, 12656, 15467, 9613, 10554, 15477, 3015, 10333, 10825, 288, 9811, 5399, 12473, 10573, 2977, 1803, 16145, 16147, 15861, 10404, 15839, 16056, 10295, 10315, 10071, 15756, 892, 11610, 10915, 15760, 16027, 16359, 13844, 5398, 9908, 10346, 10298, 15403, 10340, 11597, 15316, 10972, 1883, 15780, 16279, 15913, 16003, 10630, 16129, 800, 16383, 11051, 12642, 11706, 332, 10284, 15324, 15995, 13992, 15687, 15677, 16563, 16009, 1135, 15634, 16025, 11770, 13642, 1884, 1885, 1886, 12458, 16371, 9946, 9898, 1033, 16123, 11140, 16402, 3055, 1547, 9620, 15568, 1136, 1319, 10926, 9628, 11558, 10866, 10690, 15146, 1834, 1034, 14302, 1835, 11865, 14183, 9466, 15463, 15102, 1623, 11542, 11429, 10296, 13978, 5302, 9823, 15332, 8754, 8755, 8756, 11001, 8759, 15671, 16446, 8761, 8762, 8758, 8763, 8764, 8766, 8767, 8768, 8765, 9840, 8770, 236, 10311, 893, 1691, 10534, 14322, 1646, 11550, 1647, 672, 1385, 15975, 10190, 1359, 16187, 12489, 10279, 673, 15622, 12156, 15241, 9838, 1804, 1088, 13970, 9223, 14306, 11330, 14327, 11798, 11735, 15261, 11639, 9476, 5276, 10587, 10517, 16159, 16057, 674, 10686, 9988, 15320, 13775, 15706, 14324, 1573, 1753, 11364, 9781, 11320, 886, 10998, 8923, 13908, 15612, 10888, 10854, 15695, 15389, 15543, 15712, 15648, 9602, 1574, 5334, 1427, 11641, 11804, 1429, 1430, 9417, 9523, 10484, 11707, 16536, 12204, 15395, 14971, 1754, 15697, 13948, 10050, 12624, 14600, 15375, 8183, 8191, 9471, 9724, 15498, 16013, 1873, 959, 10931, 12616, 961, 10646, 12450, 9885, 10858, 8922, 9801, 15644, 9922, 2978, 1045, 15510, 10127, 13984, 11029, 16386, 16382, 10038, 895, 10384, 15894, 9622, 2961, 5395, 13933, 10595, 1624, 10421, 9319, 15263, 5339, 12035, 16199, 1431, 15014, 1788, 15173, 11322, 10418, 11979, 5311, 1505, 12214, 10408, 11087, 8926, 759, 15268, 3016, 15419, 1888, 11702, 13791, 14257, 1692, 10991, 12722, 13208, 9221, 339, 1432, 3123, 694, 695, 10177, 1090, 11463, 12210, 10929, 11723, 9777, 13838, 10281, 10280, 15879, 10348, 1091, 13734, 1092, 10643, 10482, 9626, 10628, 15294, 15163, 12109, 16286, 16021, 5107, 10282, 16483, 9624, 16509, 9937, 12451, 11845, 9623, 15732, 9625, 1507, 11047, 1649, 10381, 3061, 10582, 16201, 10710, 15572, 16741, 15722, 13646, 10696, 9998, 13795, 15699, 16575, 13801, 15191, 11982, 12097, 15618, 15794, 10469, 15751, 11009, 16573, 13693, 10989, 15338, 13946, 12212, 11635, 9621, 447, 12593, 14285, 15197, 11433, 15553, 1626, 15796, 12111, 9750, 10043, 10688, 11113, 13773, 14300, 15479, 15798, 16538, 10990, 11045, 11139, 11077, 15348, 10450, 10163, 10538, 12690, 10824, 14328, 11131, 1386, 12186, 15673, 8927, 16452, 1137, 350, 801, 9960, 15249, 1508, 3111, 1650, 10312, 12459, 15358, 10569, 2979, 2980, 2981, 2982, 2983, 10924, 8310, 9003, 2984, 11481, 16555, 10923, 14570, 2985, 10665, 10054, 5112, 15764, 16151, 1756, 927, 12228, 16400, 1651, 13856, 1693, 11779, 10466, 1757, 14002, 15811, 1758, 8924, 1759, 698, 16736, 11480, 241, 965, 14316, 13761, 15265, 15661, 10283, 11135, 8156, 11343, 10395, 10980, 13644, 15859, 11719, 16125, 16193, 15545, 16119, 5098, 16733, 1093, 9843, 13005, 10829, 15243, 10117, 1836, 9755, 13854, 15144, 15230, 11983, 15233, 15220]

slurl = lambda n : 'https://www.govinfo.gov/content/pkg/COMPS-'+str(n)+'/uslm/COMPS-'+str(n)+'.xml'

def findPLN(text):
  congress = text.split('</congress>')[0].split('<congress>')[1]
  n = text.split('</docNumber>')[0].split('<docNumber>')[1]
  return congress + '-' + n

# for tn in range(1, 3000):
#   n = SALnums[tn]
#   print(tn)
#   with requests.get(slurl(n)) as x:
#     try:
#       pln = findPLN(x.text)
#       t = findTitles(x.text)
#       print(pln, t)
#     except:
#       pass

# for cn in range(104, 118):
#   congress = str(cn)
#   for PLnumber in range(1, 1000):
#     file1 = open("map.txt", "a")  # append mode
#     PLtext = str(PLnumber)
#     with requests.get('https://www.congress.gov/'+congress+'/plaws/publ'+PLtext+'/PLAW-'+congress+'publ'+PLtext+'.htm') as x:
#       if (x.status_code != 200):
#         break
#       t = findTitles(x.text)
#       print(congress+'-'+PLtext, t)
#       file1.write(congress+'-'+PLtext+' '+str(t)+'\n')
      # file1.close()

with open('./SAL Compilations/65.txt') as f:
    acts = f.readlines()
    for a in acts:
      n = a.split(' ')[2]
      t = findTitles(a)
      print(str(n), t)
