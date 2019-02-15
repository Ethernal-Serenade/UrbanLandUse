import numpy as np
import util_rasters
import datetime
import csv

def calc_confusion(Yhat,Y,categories,silent=False):
    n_categories = len(categories)
    confusion = np.zeros((n_categories,n_categories),dtype='uint32')
    for j in range(n_categories):
        for i in range(n_categories):
            confusion[j,i] = np.sum(np.logical_and((Yhat==categories[i]),(Y==categories[j])))
            # print j,i, confusion[j,i], categories[j], categories[i] 
        print categories[j], np.sum(confusion[j,:])
    if not silent:
	    print confusion
	    print confusion.sum(), confusion.trace(), confusion.trace()/float(confusion.sum())
    return confusion


def calc_confusion_details(confusion):
    n_categories = confusion.shape[0]
    # out of samples in category, how many assigned to that category
    # (true positives) / (true positives + false negatives)
    # (correct) / (samples from category)
    recalls = np.zeros(n_categories, dtype='float32')
    # out of samples assigned to category, how many belong to that category
    # (true positives) / (true positives + false positives)
    # (correct) / (samples assigned to category)
    precisions = np.zeros(n_categories, dtype='float32')

    for j in range(n_categories):
        ascribed = np.sum(confusion[:,j])
        actual = np.sum(confusion[j,:])
        correct = confusion[j,j]
        recalls[j] = float(correct)/float(actual)
        precisions[j] = float(correct)/float(ascribed)

    # what percentage of total samples were assigned to the correct category
    accuracy = confusion.trace()/float(confusion.sum())

    return recalls, precisions, accuracy

def extract_scoring_arrays(Yhat_img, Y_img, categories, remapping=None):
	if isinstance(Yhat_img, str):
		Yhat_img,_,_,_,_=util_rasters.load_geotiff(Yhat_img,dtype='uint8')
	if isinstance(Y_img, str):
		Y_img,_,_,_,_=util_rasters.load_geotiff(Y_img,dtype='uint8')
	# validate inputs
	assert Y_img.ndim==2
	# assert Y_img.dtype=='uint8'
	assert Y_img.dtype==Yhat_img.dtype
	assert Y_img.shape==Yhat_img.shape
	# remap ground-truth (Y) to match output (Yhat) categories
	if remapping is not None:
		if isinstance(remapping, str):
			if remapping.lower() == '3cat' or remapping.lower() == '3category':
				remapping = {2:2,3:2,4:2,5:2}
			elif remapping.lower()=='roads':
				remapping = {0:0,1:0,2:0,3:0,4:0,5:0,6:1}
			else:
				raise ValueError('Unrecognized remapping identifier: ',remapping)
        assert isinstance(remapping, dict)
        for k in sorted(remapping.iterkeys()):
            Y_img[Y_img==k]=remapping[k]
	# create mask for presence of ground-truth (can include/exclude certain values if desired)
	mask = np.zeros(Y_img.shape, dtype='uint8')
	for c in categories:
		mask |= (Y_img == c)
    # identify and remove padding pixels
	nonpadding = (Yhat_img!=254)
	mask &= nonpadding
	# convert mask into series of locations (ie coordinates)
	locs = np.where(mask)
	# use coordinates to pull values from input images into arrays
	Yhat = Yhat_img[locs]
	Y = Y_img[locs]
	return Yhat, Y


def record_model_creation(
        model_id, notes, place_images, ground_truth, resolution, stack_label, feature_count, window, category_map, balancing, 
        model_summary, epochs, batch_size,
        train_confusion, train_recalls, train_precisions, train_accuracy, 
        train_f_score_open, train_f_score_nonres, train_f_score_res, train_f_score_roads, train_f_score_average,
        valid_confusion, valid_recalls, valid_precisions, valid_accuracy,
        valid_f_score_open, valid_f_score_nonres, valid_f_score_res, valid_f_score_roads, valid_f_score_average,
        datetime=datetime.datetime.now(),
        scorecard_file='/data/phase_iv/models/scorecard_phase_iv_models.csv'):
    
    with open(scorecard_file, mode='a') as scorecard:
        score_writer = csv.writer(scorecard, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)

        score_writer.writerow([
            model_id, notes, datetime, place_images, ground_truth, resolution, stack_label, feature_count, window, category_map, balancing, 
            model_summary, epochs, batch_size,
            train_confusion, train_recalls[0], train_recalls[1], train_recalls[2], train_recalls[3], train_precisions[0], train_precisions[1], train_precisions[2], train_precisions[3], train_accuracy, 
            train_f_score_open, train_f_score_nonres, train_f_score_res, train_f_score_roads, train_f_score_average,
            valid_confusion, valid_recalls[0], valid_recalls[1], valid_recalls[2], valid_recalls[3], valid_precisions[0], valid_precisions[1], valid_precisions[2], valid_precisions[3], valid_accuracy, 
            valid_f_score_open, valid_f_score_nonres, valid_f_score_res, valid_f_score_roads, valid_f_score_average,
            ])
    print 'model scorecard updated'
    return

def record_model_application(
        model_id, notes, place_images, ground_truth, resolution, stack_label, feature_count, window, category_map, 
        train_confusion, train_recalls, train_precisions, train_accuracy, 
        f_score_open, f_score_nonres, f_score_res, f_score_roads, f_score_average,
        datetime=datetime.datetime.now(),
        scorecard_file='/data/phase_iv/models/scorecard_phase_iv_runs.csv'):
    with open(scorecard_file, mode='a') as scorecard:
        score_writer = csv.writer(scorecard, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)

        score_writer.writerow([
            model_id, notes, datetime, place_images, ground_truth, resolution, stack_label, feature_count, window, category_map,
            confusion, recalls[0], recalls[1], recalls[2], recalls[3], precisions[0], precisions[1], precisions[2], precisions[3], accuracy, 
            f_score_open, f_score_nonres, f_score_res, f_score_roads, f_score_average,
            ])
    print 'run scorecard updated'
    return