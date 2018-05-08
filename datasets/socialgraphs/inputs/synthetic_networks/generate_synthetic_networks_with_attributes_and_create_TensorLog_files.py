import networkx as nx
import random


ROOT_PATH = '../../inputs/'

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
		
	# print(source_targets)
	return source_targets	

def create_cfacts_file(graph_name, fact_ids, id_labels, source_targets, attribute_match_prob):

	labels_set = set(id_labels.values())
	facts_file_path = ROOT_PATH + graph_name+ '.cfacts' # friend	rightrainbow.com	volokh.com... label	tomburka.com	Liberal
	#label	jinkythecat.blogspot.com	Liberal
	with open(facts_file_path, 'w') as fact_file:
		for id, label in id_labels.iteritems():
			if id in fact_ids:
				fact_file.write('label'+ '\t'+ 'node_' +str(id) +'\t'+ chr(int(id_labels[id])+64) + '\n' )

			# With a probability, we write the right attribute
			# else write the wrong attribute
			# likes_tag
			if attribute_match_prob >= 0.5: # for less generate data without attributes
				if random.random()< attribute_match_prob:
					fact_file.write('likes_tag'+ '\t'+ 'node_' +str(id) +'\t'+ chr(int(id_labels[id])+64) + '\n' )
				else:
					# print(labels_set)
					labels_list = list(labels_set)
					labels_list.remove(label)
					# print(labels_list)
					fact_file.write('likes_tag'+ '\t'+ 'node_' +str(id) +'\t'+ chr(int(random.choice(labels_list))+64) + '\n' )
				
					# print(id)
					# targets = source_targets[id]
					# for target in targets:
					# 	fact_file.write('friend' + '\t'+ str(id)+ '\t' + str(target) + '\n')	
			else:
				if id in fact_ids:
					fact_file.write('likes_tag'+ '\t'+ 'node_' +str(id) +'\t'+ chr(int(id_labels[id])+64) + '\n' )

	# all relations should go in facts file			
	with open(facts_file_path, 'a') as fact_file:
		for source, targets in source_targets.iteritems():
			for target in targets:
				fact_file.write('friend' + '\t'+ 'node_' +str(source) + '\t' + 'node_' +str(target) + '\n')		

def create_train_test_examples(graph_name, train_ids, test_ids, id_labels):
	train_file_path = ROOT_PATH + graph_name+ '-train.exam' # inferred_label	rightrainbow.com	Conservative
	test_file_path = ROOT_PATH + graph_name+ '-test.exam' # inferred_label	rightrainbow.com	Conservative

	with open(train_file_path, 'w') as train_file:
	    for user in train_ids:
	        train_file.write('inferred_label' + '\t' + 'node_' +str(user) + '\t' + chr(int(id_labels[user])+64) + '\n')
	    
	with open(test_file_path, 'w') as test_file:
	    for user in test_ids:
	        test_file.write('inferred_label' + '\t' + 'node_' +str(user) + '\t' + chr(int(id_labels[user])+64) + '\n')



def generate_networks(graph_name, num_of_comm, nodes_in_each_comm,\
 	in_cluster_prob, out_cluster_probab, attribute_match_prob):

	G = nx.planted_partition_graph(num_of_comm, nodes_in_each_comm,\
	 in_cluster_prob, out_cluster_probab, seed=42)
	# G.nodes()
	# G.edges()
	# G.graph['partition']
	# [set([0, 1, 2]), set([3, 4, 5]), set([8, 6, 7]), set([9, 10, 11])]

	id_labels, ids = get_labels(G)
	print('id_labels length', len(id_labels))

	source_targets = get_edges(G)
	print('source_targets length', len(source_targets))


	random.shuffle(ids)
	fact_ids = ids[:int(0.5* len(ids))]
	# print(fact_ids)
	train_ids = ids[int(0.5* len(ids)) + 1:int(0.8* len(ids))]
	test_ids = ids[int(0.8* len(ids)) + 1:]


	create_cfacts_file(graph_name, fact_ids, id_labels,source_targets, attribute_match_prob)
	create_train_test_examples(graph_name, train_ids,test_ids, id_labels)


mean_c = 8.0
n = 1000

for prob in range(4, 10, 1):
	attribute_match_prob = 0.1 * prob
	for c_in_minus_c_out in range(0, 16, 2):

		c_in = mean_c + 1.0*c_in_minus_c_out/2
		c_out = mean_c - 1.0*c_in_minus_c_out/2
		p_in = 1.0*c_in/n
		p_out = 1.0*c_out/n	

		print(c_in, c_out)
		print(p_in, p_out)


		# p_in = 0.5
		# p_out = 0.1	
		num_of_comm = 2
		nodes_in_each_comm = int(1.0*n/num_of_comm)

		graph_name = 'planted_partition_with_attributes_'\
		 + str(n) + '_'+ '{:04.1f}'.format(c_in_minus_c_out) + '_' \
		 + str(c_in) + '_' + str(c_out) + '_' + str(attribute_match_prob)

		generate_networks(graph_name, num_of_comm, nodes_in_each_comm, p_in, p_out, attribute_match_prob)
