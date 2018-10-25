'''
This script is used to load a saved checkpoint in order to find
the B-matrix, action normalization parameters, and goal state
encoding. This script is called prior to performing flow control,
as they are required to perform MPC.

Note that all paths are specific to the machine on which the 
code was run and need to be updated accordingly.
'''

import os, sys
import h5py
import tensorflow as tf
import numpy as np
import pickle

from koopman_model import KoopmanModel

# Read in args
with open('/home/sisl/jeremy/deep_cfd/koopman/args.pkl', 'rb') as f:                                                                                                                                                            
    args = pickle.load(f)

# Construct model
net = KoopmanModel(args)

# Begin session and assign parameter values
with tf.Session() as sess:
    tf.global_variables_initializer().run()
    saver = tf.train.Saver(tf.global_variables(), max_to_keep=5)
    ckpt_name = sys.argv[1]
    saver.restore(sess, '/home/sisl/jeremy/deep_cfd/koopman/' + args.save_dir + '/' + ckpt_name)

    # Find B-matrix (will be constant)
    B = sess.run(net.B)[0].T
    shift_u = sess.run(net.shift_u)
    scale_u = sess.run(net.scale_u)

    # To find goal state, find encoding of steady base flow at Re50
    x = np.zeros((args.batch_size*(args.seq_length+1), 128, 256, 4), dtype=np.float32)
    u = np.zeros((args.batch_size, args.seq_length, args.action_dim), dtype=np.float32)

    # Load solution for base flow
    f = h5py.File('/raid/jeremy/' + sys.argv[2] + '/sol_data/sol_data_0000.h5', 'r')
    x[0] = np.array(f['sol_data'])

    # Normalize data
    x = (x - sess.run(net.shift))/sess.run(net.scale)

    # Run inputs through network, find encoding
    feed_in = {}
    feed_in[net.x] = x
    feed_in[net.u] = u
    feed_out = net.code_x
    code_x = sess.run(feed_out, feed_in)

    # Define goal state
    goal_state = code_x[0]

    # Save quantities to file
    f = h5py.File('./matrices_misc.h5', 'w')
    f['B'] = B
    f['shift_u'] = shift_u
    f['scale_u'] = scale_u
    f['goal_state'] = goal_state
    f.close()    