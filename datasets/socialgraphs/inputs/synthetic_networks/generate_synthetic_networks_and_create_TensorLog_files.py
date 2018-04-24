import networkx as nx
import random



def get_labels(G):
	ids = G.nodes()
	id_labels = {}

	sets = G.graph['partition']
	no_of_sets = len(sets)

	for i in range(1, no_of_sets + 1):
		#[set([0, 1, 2]), set([3, 4, 5]), set([8, 6, 7]), set([9, 10, 11])]
		nodes_set = sets[i-1]
		for node_id in list(nodes_set):
			id_labels[node_id] = i

	# print('Number of total users', len((ids)))
	return id_labels, ids

def update_source_target_dictionary(source_targets, source, target):
	if source not in source_targets:
		source_targets[source] = []

	targets = source_targets[source]
	targets.append(target)
	source_targets[source] = targets

	return source_targets

def get_edges(G):
	source_targets = {}
	for source, target in G.edges():
		source_targets = \
			update_source_target_dictionary(source_targets, source, target)

		source_targets = \
			update_source_target_dictionary(source_targets, target, source)
		
	print(source_targets)
	return source_targets	

def create_cfacts_file(fact_ids, id_labels, source_targets):
	facts_file_path = '../planted_partition.cfacts' # friend	rightrainbow.com	volokh.com... label	tomburka.com	Liberal
	#label	jinkythecat.blogspot.com	Liberal
	with open(facts_file_path, 'a') as fact_file:
		for id, label in id_labels.iteritems():
			if id in fact_ids:
				fact_file.write('label'+ '\t'+ 'node_' +str(id) +'\t'+ chr(int(id_labels[id])+64) + '\n' )

				# print(id)
				# targets = source_targets[id]
				# for target in targets:
				# 	fact_file.write('friend' + '\t'+ str(id)+ '\t' + str(target) + '\n')		

	# all relations should go in facts file			
	with open(facts_file_path, 'a') as fact_file:
		for source, targets in source_targets.iteritems():
			for target in targets:
				fact_file.write('friend' + '\t'+ 'node_' +str(source) + '\t' + 'node_' +str(target) + '\n')		

def create_train_test_examples(train_ids, test_ids, id_labels):
	train_file_path = '../planted_partition-train.exam' # inferred_label	rightrainbow.com	Conservative
	test_file_path = '../planted_partition-test.exam' # inferred_label	rightrainbow.com	Conservative

	with open(train_file_path, 'a') as train_file:
	    for user in train_ids:
	        train_file.write('inferred_label' + '\t' + 'node_' +str(user) + '\t' + chr(int(id_labels[user])+64) + '\n')
	    
	with open(test_file_path, 'a') as test_file:
	    for user in test_ids:
	        test_file.write('inferred_label' + '\t' + 'node_' +str(user) + '\t' + chr(int(id_labels[user])+64) + '\n')


G = nx.planted_partition_graph(2, 8, 0.5, 0.1,seed=42)
G.nodes()
G.edges()
G.graph['partition']
# [set([0, 1, 2]), set([3, 4, 5]), set([8, 6, 7]), set([9, 10, 11])]


id_labels, ids = get_labels(G)
print(len(id_labels))

source_targets = get_edges(G)
print(len(source_targets))


random.shuffle(ids)
fact_ids = ids[:int(0.5* len(ids))]
print(fact_ids)
train_ids = ids[int(0.5* len(ids)) + 1:int(0.8* len(ids))]
test_ids = ids[int(0.8* len(ids)) + 1:]


create_cfacts_file(fact_ids, id_labels,source_targets)
create_train_test_examples(train_ids,test_ids, id_labels)
