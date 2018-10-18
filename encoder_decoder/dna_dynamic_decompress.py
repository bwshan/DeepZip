# 
# Decompression application using adaptive arithmetic coding
# 
# Usage: python adaptive-arithmetic-decompress.py InputFile OutputFile
# This decompresses files generated by the adaptive-arithmetic-compress.py application.
# 
# Copyright (c) Project Nayuki
# 
# https://www.nayuki.io/page/reference-arithmetic-coding
# https://github.com/nayuki/Reference-arithmetic-coding
# 

import sys
import arithmeticcoding
python3 = sys.version_info.major >= 3
import numpy as np
from keras.preprocessing.sequence import pad_sequences
import os,sys
import json
from keras.models import load_model
from keras.models import Sequential
from keras.layers import Dense
from keras.layers import LSTM, Flatten, CuDNNLSTM
from math import sqrt
from keras.layers.embeddings import Embedding
# from matplotlib import pyplot
import keras

def softmax(x):
    """Compute softmax values for each sets of scores in x."""
    e_x = np.exp(x - np.max(x))
    return e_x / e_x.sum()


def generate_probability(n_classes):
	return softmax(np.random.uniform(10, 11, n_classes))

def softmax(x):
    """Compute softmax values for each sets of scores in x."""
    e_x = np.exp(x - np.max(x))
    return e_x / e_x.sum()


# Command line main application function.
def main(args):
	# Handle command line arguments
	if len(args) != 2:
		sys.exit("Usage: python adaptive-arithmetic-decompress.py InputFile OutputFile")
	inputfile, outputfile = args


	classes = 5
	seqlen = 60
	old_model = load_model('model.h5')
	wts = old_model.get_weights()
	model = Sequential()
	model.add(Embedding(classes, 32, batch_input_shape=(1, seqlen)))
	model.add(CuDNNLSTM(32, batch_input_shape=(1, seqlen, 8), stateful=False, return_sequences=True))
	model.add(CuDNNLSTM(32, batch_input_shape=(1, seqlen, 8), stateful=False, return_sequences=True))
	# model.add(LSTM(128, stateful=False, return_sequences=True))
	model.add(Flatten())
	model.add(Dense(64, activation='relu'))
	# model.add(Activation('tanh'))
	# model.add(Dense(10, activation='relu'))
	# model.add(BatchNormalization())
	model.add(Dense(classes, activation='softmax'))
	optim = keras.optimizers.Adam(lr=1e-3, beta_1=0.9, beta_2=0.999, epsilon=None, decay=0.0, amsgrad=False)
	model.compile(loss=keras.losses.categorical_crossentropy, optimizer=optim)

	model.set_weights(wts)

	# Perform file decompression
	with open(inputfile, "rb") as inp, open(outputfile, "wb") as out:
		bitin = arithmeticcoding.BitInputStream(inp)
		decompress(bitin, out, model)


def decompress(bitin, out, model):
	dec = arithmeticcoding.ArithmeticDecoder(32, bitin)
	probs = np.load('prob.npy').astype(np.float32)
	i = 0
	output = []
	zeroes = np.zeros((1, 60))
	data = np.load('chr1.npy').reshape(-1)
	output = list(data[:60])
	while True:
		# Decode and write one byte
		z = i
		data = np.array(output[z:z+60]).astype(np.int64)
		# data = data.reshape(1, -1)
		print(i)
		zeroes[0] = data
		prob = model.predict(zeroes, batch_size=1)[0]
		i += 1
		l = [int(p*10000000+1) for p in prob]
		l.append(1)
		# print(l)
		freqs = arithmeticcoding.SimpleFrequencyTable(l)
		symbol = dec.read(freqs)
		print(symbol)
		# print(symbol)
		output.append(symbol)
		if symbol == 5:  # EOF symbol
			break
		out.write(str(symbol))
	output = np.array(output)
	np.save('output', output)
		# freqs.increment(symbol)


# Main launcher
if __name__ == "__main__":
	main(sys.argv[1 : ])