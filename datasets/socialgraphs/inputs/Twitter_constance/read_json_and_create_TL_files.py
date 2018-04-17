import json
import pandas as pd 
import random

# Define global variables
PRO_HILLARY = 'ProHillary'
PRO_TRUMP = 'ProTrump'
NEUTRAL = 'Neutral'


read_all_tweets = []
with open('./Twitter_users.json', 'r') as f_read:
    for line in f_read:
        read_all_tweets.append(json.loads(line))

print('Number of all tweets in file: ' , len(read_all_tweets))



def get_labels():
	train_tweets = pd.read_csv("./annotation_data/development_annotations.csv",dtype={"tid":"str"})
	test_tweets = pd.read_csv("./annotation_data/validation_annotations.csv",dtype={"tid":"str"})
	print test_tweets.shape
	print train_tweets.shape

	amt_annotations = pd.read_csv("./annotation_data/amt_annotations.csv",dtype={"tid":"str"})

	ids = []
	id_targt_rating = {}

	for index, row in amt_annotations.iterrows():
	   
	#     print(row['tid'], row['target'] , row['tertiary_rating'])
	    ids.append(row['tid'])
	    id_targt_rating[row['tid']] = row['target'] +'_' + str(row['tertiary_rating'])
	#     if i > 10:
	#         break

	ids_set = set(ids)
	# print(len(ids))        
	print('Number of total users', len((ids_set)))
	# print(id_targt_rating)
	return id_targt_rating


# For Twitter Social Network Analysis
# Problem: Label Twitter User as ProHillary or ProTrump

# Data:
# Tweets with User, Tweetstext, mention, # tag

# Derived data:
# Sentiment in Tweet text


# inferred_label(X,Y) <= influenced_by(X,Z) & label(Z,Y)
# influenced_by(A,B) <= friend(A,Z) & influenced_by(Z,B)
# influenced_by(A,B) <= friend(A,B)


def create_cfacts(alltweets, id_targt_rating):
	labels = {}
	mentions = []
	mentioned_by = {}


	screen_names_in_dataset = []

	facts_file_path = './Twitter.cfacts' # friend	rightrainbow.com	volokh.com... label	tomburka.com	Liberal

	for tweet in alltweets:
	   
	#     print(tweet.id)
	    
	    screen_name = tweet['user']['screen_name']
	    screen_names_in_dataset.append(screen_name)
	    
	    target = id_targt_rating[str(tweet['id'])].split('_')[0]
	    sentiment = int(id_targt_rating[str(tweet['id'])].split('_')[1])
	    
	    # default be Neutral
	    labels[screen_name] = NEUTRAL
	    if target == 'Hillary Clinton':
	        if  sentiment > 0:
	            labels[screen_name] = PRO_HILLARY
	        elif sentiment < 0:
	            labels[screen_name] = PRO_TRUMP
	            
	    elif target == 'Donald Trump':
	        if  sentiment > 0:
	            labels[screen_name] = PRO_TRUMP
	        elif sentiment < 0:
	            labels[screen_name] = PRO_HILLARY
	            
	    with open(facts_file_path, 'a') as fact_file:    
	        #label	jinkythecat.blogspot.com	Liberal
	        fact_file.write('label'+ '\t'+ screen_name+'\t'+labels[screen_name] + '\n' )

	    
	#     print(tweet.user.screen_name)
	    
	#     for hastag in tweet.entities['hashtags']:
	#         print(screen_name, 'tags', hastag['text'])
	        
	    with open(facts_file_path, 'a') as fact_file:
	        for mention in tweet['entities']['user_mentions']:
	            fact_file.write('friend' + '\t'+ screen_name+ '\t' + mention['screen_name'] + '\n')
	            mentions.append(mention['screen_name'])
	            if mention['screen_name'] not in mentioned_by:
	                mentioned_by[mention['screen_name']] = [screen_name]
	            else:
	                mentioned_bys = mentioned_by[mention['screen_name']]
	                mentioned_bys.append(screen_name)
	                
	                mentioned_by[mention['screen_name']] = mentioned_bys
	                
	            #friend	rightrainbow.com	volokh.com


	    
	#     print(tweet.user)
	#     print(tweet.entities)
	#     if i > 200:
	#         break

	return labels, mentioned_by

def create_train_test_data(labels, mentioned_by):
	# For inferred train and test lables
	# check if majority are proTrump or ProHillary
	train_file_path = './Twitter-train.exam' # inferred_label	rightrainbow.com	Conservative
	test_file_path = './Twitter-test.exam' # inferred_label	rightrainbow.com	Conservative
	inferred_label = {}

	for mention, mentioned_bys in mentioned_by.iteritems():
	    label = NEUTRAL
	    pro_trump_count = 0
	    pro_hallary_count = 0
	    
	    for name in mentioned_bys:
	        if name in labels:
	            if labels[name] == PRO_HILLARY:
	                pro_hallary_count = pro_hallary_count +1
	            elif labels[name] == PRO_TRUMP:
	                pro_trump_count = pro_trump_count +1
	                
	    if pro_trump_count > pro_hallary_count:
	        inferred_label[mention] = PRO_TRUMP
	    elif pro_trump_count < pro_hallary_count:
	        inferred_label[mention] = PRO_HILLARY
	    else:
	        inferred_label[mention] = NEUTRAL
	        
	inferred_label_list  = list(inferred_label)
	random.shuffle(inferred_label_list)

	train_data = inferred_label_list[:int(0.8* len(inferred_label_list))]
	test_data = inferred_label_list[int(0.8* len(inferred_label_list)) + 1:]


	with open(train_file_path, 'a') as train_file:
	    for user in train_data:
	        train_file.write('inferred_label' + '\t' + user + '\t' + inferred_label[user] + '\n')
	    
	with open(test_file_path, 'a') as test_file:
	    for user in test_data:
	        test_file.write('inferred_label' + '\t' + user + '\t' + inferred_label[user] + '\n')
	    
	# print(train_data)        
	# print(test_data)
id_targt_rating = get_labels()
labels, mentioned_by_list = create_cfacts(read_all_tweets, id_targt_rating)	
create_train_test_data(labels, mentioned_by_list)

                

