# This file is excerpt of CVD_tracker:
# read it for more details and more explanations

import numpy as np
# import pandas as pd # only for demonstration!
from pickle import load
import logging
import os
from django.conf import settings

logger = logging.getLogger('django')


def data_preparation(gender, cholesterol):
	# Returns
	# Describes cholesterol as its level, based on gender of a person

	cholesterol_level = 0

	if gender == 1:
		if cholesterol > 209:
			cholesterol_level = 3
		elif cholesterol > 178:
			cholesterol_level = 2
		else:
			cholesterol_level = 1
	
	elif gender == 2:
		if cholesterol > 244:
			cholesterol_level = 3
		elif cholesterol > 207:
			cholesterol_level = 2
		else:
			cholesterol_level = 1

	# logger.info('Cholesterol: {}, gender: {}, cholesterol_level: {}'.format(cholesterol, gender, cholesterol_level))
	# digits of normal values was taken from this paper: "
	# Serum cholesterol level in normal people: association of 
	# serum cholesterol level with age and relative body weight"
	
	return cholesterol_level


# 'age', 'height', 'ap_high', 'ap_low', 'cholesterol_level', 'pulse_pressure'
def cvd_value(age, height, blood_pressure_sys, blood_pressure_dia, cholesterol_level):
	path = os.path.join(settings.BASE_DIR, 'api/pkl_models/CVD_model.pkl')
	# Code for model restoration
	with open(path, 'rb') as f:
		_, model, scaler = load(f)

	# calculate pulse pressure
	pulse = blood_pressure_sys - blood_pressure_dia
	# We should use natural log to height, before we put it into scaler
	height = np.log(height)
	# use scaler before usage of model
	x = scaler.transform(np.array([[age, height, blood_pressure_sys, blood_pressure_dia, cholesterol_level, pulse]]))
	# You can check X value: print(x)
	# use model -> take prediction
	prediction = model.predict(x)
	# logger.info('Prediction: {}'.format(prediction[0]))

	return prediction[0]
	# 1 - person have CVD
	# 0 - otherwise


# glucose, blood_pressure_dia, BMI, Age
def diabet_value(glucose, blood_pressure_dia, bmi, age):
	logger.info("Input parameters: Glucose: {}, BPD: {}, BMI: {}, Age: {}".format(glucose, blood_pressure_dia, bmi, age))
	path = os.path.join(settings.BASE_DIR, 'api/pkl_models/diabet_model.pkl')
	# Code for model restoration
	with open(path, 'rb') as f:
		_, model, scaler = load(f)

	# use scaler before usage of model
	x = scaler.transform(np.array([[glucose, blood_pressure_dia, bmi, age]]))
	# You can check X value: print(x)
	# use model -> take prediction
	prediction = model.predict(x)
	logger.info('Prediction Diabetes: {}'.format(prediction[0]))

	return prediction[0]
	# 1 - person have diabetes
	# 0 - otherwise

# age, glucose, BMI, Hypertension
def get_stroke_value(age, glucose, bmi, blood_pressure_sis , blood_pressure_dia):
	logger.info("Input parameters: Age: {}, Glucose: {}, BMI: {}, blood_pressure_sis: {}, blood_pressure_dia: {}".format(age, glucose, bmi, blood_pressure_sis, blood_pressure_dia)) 
	path = os.path.join(settings.BASE_DIR, 'api/pkl_models/stroke_model.pkl')

	#Caluclating Hypetension
	if blood_pressure_dia >= 90 and blood_pressure_sis >= 140:
		hypertension = 1
	else:
		hypertension = 0

	#default no. of rows for reshape
	number_of_rows = 1

	# Code for model restoration
	with open(path, 'rb') as f:
		_, model, scaler = load(f)

	# use scaler before usage of model
	standard_X_without_hypertension = scaler.transform(
		(np.array([[age, glucose, bmi]])))
	standard_X = np.concatenate((standard_X_without_hypertension, 
	np.array(hypertension).reshape((number_of_rows,1))), axis=1)

	# You can check standard_X value: print(standard_X)
	# use model -> take prediction
	prediction = model.predict(standard_X)
	logger.info('Prediction Stroke: {}'.format(prediction[0]))

	print("Pridiction: ", prediction[0])
	return prediction[0]
	# 1 - person have stroke risk
	# 0 - otherwise