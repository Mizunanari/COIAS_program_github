#!/usr/bin/env python3
# -*- coding: UTF-8 -*
#Timestamp: 2022/08/06 21:00 sugiura
###########################################################################################
# 新発見天体はそのデータの1行目の名前の直後にアスタリスクを付けなければいけないので, それを付与する.
#
# 入力: pre_repo3.txt
# 出力: send_mpc.txt
# 　　    アスタリスク付与後の最終的な報告ファイル.
# 　　    このファイルにヘッダー情報を付けたものを最終的にMPCにメールで報告する.
###########################################################################################
import traceback
import print_detailed_log

try:
    # detect list
    tmp1 = "pre_repo3.txt"
    tmp2 = "send_mpc.txt"
    data1 = open(tmp1, "r")

    # all object
    lines = data1.readlines()
    # identified object

    # list of moving object
    new_list1 = []
    for i in range(len(lines) - 1):
        # if lines[i][0:12] != lines[i+1][0:12] and lines[i+1][5] == 'H':
        # print(lines[i])
        # ---K. S. modify 2021/6/17--------------------------------------------------------------------------------------
        if i == 0:
            if lines[i][5:6] == 'H':
                mylist = [word for word in lines[i]]
                mylist[12] = '*'
                newlist = "".join(mylist)
                new_list1.append(newlist)
            else:
                new_list1.append(lines[i])

        if (lines[i][0:12] != lines[i + 1][0:12] and lines[i + 1][5:6] == 'H'):
            # if lines[i][0:12] != lines[i+1][0:12] and lines[i+1][5:9] == 'H002':

            # lines[i+1][13].replace(' ','*')
            mylist = [word for word in lines[i + 1]]
            mylist[12] = '*'
            newlist = "".join(mylist)
            new_list1.append(newlist)
        else:
            new_list1.append(lines[i + 1])
            # print(lines[i])
        # ---------------------------------------------------------------------------------------------------------------
    with open(tmp2, 'wt') as f:
        f.writelines(new_list1)

except FileNotFoundError:
    print("Some previous files are not found in komejirushi.py!",flush=True)
    print(traceback.format_exc(),flush=True)
    error = 1
    errorReason = 74

except Exception:
    print("Some errors occur in komejirushi.py!",flush=True)
    print(traceback.format_exc(),flush=True)
    error = 1
    errorReason = 75

else:
    error = 0
    errorReason = 74

finally:
    errorFile = open("error.txt","a")
    errorFile.write("{0:d} {1:d} 708 \n".format(error,errorReason))
    errorFile.close()

    if error==1:
        print_detailed_log.print_detailed_log(dict(globals()))
