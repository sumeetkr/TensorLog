import pandas as pd 
import random


def get_labels():
	# Node_Name,Node_Title,louvain
	node_labels = pd.read_csv("./data/Node_with_group_labels.csv",dtype={"louvain":"str"})
	# print node_labels.shape

	ids = []
	id_labels = {}

	for index, row in node_labels.iterrows():
	    ids.append(row['Node_Name'])
	    id_labels[row['Node_Name']] = row['louvain']
	
	print('Number of total users', len((ids)))
	return id_labels, ids

def get_edges():
	# read line by line
	# smoneill59,DrexHawken,DailyCaller,smoneill59,MergeRightGOP
	source_targets = {}
	edges_file = "./data/Network-edges.csv"
	with open(edges_file, 'r') as f_edges:
		for line in f_edges:
			line = line.strip()
			source = line.split(',')[0]
			targets = line.split(',')[1:]
			source_targets[source] = targets

	return source_targets

def create_cfacts_file(fact_ids, id_labels, source_targets):
	facts_file_path = './EchoChamber.cfacts' # friend	rightrainbow.com	volokh.com... label	tomburka.com	Liberal
	#label	jinkythecat.blogspot.com	Liberal
	with open(facts_file_path, 'a') as fact_file:
		for id, label in id_labels.iteritems():
			if id in fact_ids:
				fact_file.write('label'+ '\t'+ id+'\t'+id_labels[id] + '\n' )

	with open(facts_file_path, 'a') as fact_file:
		for source, targets in source_targets.iteritems():
			for target in targets:
				fact_file.write('friend' + '\t'+ source+ '\t' + target + '\n')		


def create_train_test_examples(train_ids, test_ids, id_labels):
	train_file_path = './EchoChamber-train.exam' # inferred_label	rightrainbow.com	Conservative
	test_file_path = './EchoChamber-test.exam' # inferred_label	rightrainbow.com	Conservative

	with open(train_file_path, 'a') as train_file:
	    for user in train_ids:
	        train_file.write('inferred_label' + '\t' + user + '\t' + id_labels[user] + '\n')
	    
	with open(test_file_path, 'a') as test_file:
	    for user in test_ids:
	        test_file.write('inferred_label' + '\t' + user + '\t' + id_labels[user] + '\n')

id_labels, ids = get_labels()
print(len(id_labels))

source_targets = get_edges()
print(len(source_targets))

random.shuffle(ids)
fact_ids = ids[:int(0.3* len(ids))]
train_ids = ids[int(0.3* len(ids)) + 1:int(0.8* len(ids))]
test_ids = ids[int(0.8* len(ids)) + 1:]


create_cfacts_file(fact_ids, id_labels,source_targets)
create_train_test_examples(train_ids,test_ids, id_labels)

# Take some random ids to put in cfacts
# Take 0.8 of rest into train examples
# Take 0.2 of rest into test examples
# Put all grap edges in cfact




# labels, mentioned_by_list = create_cfacts(read_all_tweets, id_targt_rating)	
# create_train_test_data(labels, mentioned_by_list)

                

