#!/usr/bin/python3
# encoding: utf-8
'''
@author: matthew hsw
@contact: murdockhou@gmail.com
@software: pycharm
@file: encoder_test.py
@time: 2019/7/23 下午3:34
@desc:
'''

import cv2
import numpy as np
import os

use_dataset = False

if use_dataset:
    import tensorflow as tf
    from decoder.decode_spm import SpmDecoder
    from dataset.dataset import get_dataset
    from config.center_config import center_config
    os.environ['CUDA_VISIBLE_DEVICES'] = '-1'

    dataset = get_dataset()
    colors = [[0,0,255],[255,0,0],[0,255,0]]

    for epco in range(1):
        for step, (img, label) in enumerate(dataset):
            # print (step)
            # print (img[0].shape)
            # img1 = img[0]
            # label1 = label[0]
            # break
            print ('epoch {} / step {}'.format(epco, step))
            img = (img.numpy()[0] * 255).astype(np.uint8)

            label = label[0]

            spm_decoder = SpmDecoder(4, 4, center_config['height']//4, center_config['width']//4)
            joints, centers = spm_decoder(label)

            for j,  single_person_joints in enumerate(joints):
                cv2.circle(img, (int(centers[j][0]), int(centers[j][1])), 8, colors[j%3], thickness=-1)
                for i in range(14):
                    x = int(single_person_joints[2*i])
                    y = int(single_person_joints[2*i+1])
                    cv2.circle(img, (x,y),4,colors[j%3],thickness=-1)
                    cv2.putText(img, str(i), (x,y), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 0, 250), 1)
            cv2.imshow('label', img)
            k = cv2.waitKey(0)
            if k == 113:
                break

# test on label without dataset
else:
    from utils.utils import *
    from config.center_config import center_config as params
    from encoder.spm import SingleStageLabel
    from decoder.decode_spm import SpmDecoder
    json_file = '/media/hsw/E/datasets/ai_challenger_keypoint_train_20170909/train10.json'
    img_path = '/media/hsw/E/datasets/ai_challenger_keypoint_train_20170909/keypoint_train_images_20170902'
    img_ids, id_annos_dict, id_kps_dict = read_json(json_file)
    colors = [[0,0,255],[255,0,0],[0,255,0]]
    for img_id in img_ids:
        print ('--------------------------------------------------------------')
        bboxs = id_annos_dict[img_id]
        kps = id_kps_dict[img_id]
        img = cv2.imread(os.path.join(img_path, img_id + '.jpg'))

        img_ori = img.copy()
        for box in bboxs:
            print(box)
            cv2.rectangle(img_ori, (int(box[0]), int(box[1])), (int(box[2]), int(box[3])), color=(0, 0, 255))

        for j, kp in enumerate(kps):
            for i in range(14):
                x = int(kp[i*3])
                y = int(kp[i*3+1])
                v = kp[i*3+2]
                cv2.circle(img_ori, (x,y),4,colors[j%3],thickness=-1)
        #  data aug
        # img, bboxs, kps = data_aug(img, bboxs, None)

        # padding img
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        h, w, c = img.shape
        # 只在最右边或者最下边填充0, 这样不会影响box或者点的坐标值, 所以无需再对box或点的坐标做改变
        if w > h:
            img = cv2.copyMakeBorder(img, 0, w-h, 0, 0, cv2.BORDER_CONSTANT, value=(0, 0, 0))
        else:
            img = cv2.copyMakeBorder(img, 0, 0, 0, h-w, cv2.BORDER_CONSTANT, value=(0, 0, 0))

        # create center label
        orih, oriw, oric = img.shape
        neth, netw = params['height'], params['width']
        outh, outw = neth // params['scale'], netw // params['scale']

        centers, sigmas, whs = prepare_bbox(bboxs, orih, oriw, outh, outw)
        for center in centers:
            print ("ori center: ", center)
        keypoints, kps_sigmas = prepare_kps(kps, orih, oriw, outh, outw)

        spm_encoder = SingleStageLabel(outh, outw, centers, sigmas, keypoints)
        spm_label = spm_encoder()

        factor_x = netw / outw
        facotr_y = neth / outh
        spm_decoer = SpmDecoder(factor_x, facotr_y, outw, outh)
        joints, decode_centers = spm_decoer([spm_label[...,0:1], spm_label[...,1:2*14+1]])

        # create img input
        img = cv2.resize(img, (netw, neth), interpolation=cv2.INTER_CUBIC)

        for center in decode_centers:
            print(center)
        #     x = int(center[0])
        #     y = int(center[1])
        #     print ('center: ', x, y)
        #     cv2.circle(img, (x, y), 8, (0,0,255), thickness=-1)

        for single_person_joints in joints:
            # print(kps)
            for i in range(14):
                x = int(single_person_joints[2*i])
                y = int(single_person_joints[2*i+1])
                cv2.circle(img, (x,y), 4, (0,255,0),thickness=-1)
        cv2.imshow('label', img)
        cv2.imshow('ori', img_ori)
        k = cv2.waitKey(0)
        if k == 113:
            break


