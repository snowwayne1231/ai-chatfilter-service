from __future__ import absolute_import, division, print_function, unicode_literals

import tensorflow as tf

import tensorflow_datasets as tfds
import os

DIRECTORY_URL = 'https://storage.googleapis.com/download.tensorflow.org/data/illiad/'
FILE_NAMES = ['cowper.txt', 'derby.txt', 'butler.txt']

for name in FILE_NAMES:
    text_dir = tf.keras.utils.get_file(name, origin=DIRECTORY_URL+name)
  
parent_dir = os.path.dirname(text_dir)

def labeler(example, index):
    return example, tf.cast(index, tf.int64)

labeled_data_sets = []

for i, file_name in enumerate(FILE_NAMES):
    lines_dataset = tf.data.TextLineDataset(os.path.join(parent_dir, file_name))
    labeled_dataset = lines_dataset.map(lambda ex: labeler(ex, i))
    labeled_data_sets.append(labeled_dataset)

BUFFER_SIZE = 50000
BATCH_SIZE = 64
TAKE_SIZE = 5000

all_labeled_data = labeled_data_sets[0]
for labeled_dataset in labeled_data_sets[1:]:
    all_labeled_data = all_labeled_data.concatenate(labeled_dataset)
  
all_labeled_data = all_labeled_data.shuffle(
    BUFFER_SIZE, reshuffle_each_iteration=False)

tokenizer = tfds.features.text.Tokenizer()


for ex, _ in all_labeled_data.take(20):
    
    # print(ex)
    # print(_)
    some_tokens = tokenizer.tokenize(ex.numpy())
    # print(some_tokens)


print('========= vocabulary ===========')

vocabulary_set = set()
for text_tensor, _ in all_labeled_data:
  some_tokens = tokenizer.tokenize(text_tensor.numpy())
  vocabulary_set.update(some_tokens)
  

vocab_size = len(vocabulary_set)
print(vocab_size)



encoder = tfds.features.text.TokenTextEncoder(vocabulary_set)

# example_text = next(iter(all_labeled_data))[0].numpy()

# encoded_example = encoder.encode(example_text)



def encode(text_tensor, label):
    encoded_text = encoder.encode(text_tensor.numpy())
    return encoded_text, label

def encode_map_fn(text, label):
    return tf.py_function(encode, inp=[text, label], Tout=(tf.int64, tf.int64))

all_encoded_data = all_labeled_data.map(encode_map_fn)

print('========= check all_encoded_data =========')
for ex, _ in all_encoded_data.take(20):
    print(ex.numpy())

train_data = all_encoded_data.skip(TAKE_SIZE).shuffle(BUFFER_SIZE)
train_data = train_data.padded_batch(BATCH_SIZE, padded_shapes=([-1],[]))

test_data = all_encoded_data.take(TAKE_SIZE)
test_data = test_data.padded_batch(BATCH_SIZE, padded_shapes=([-1],[]))

sample_text, sample_labels = next(iter(test_data))

# print(sample_text[0])
# print(sample_labels[0])

vocab_size += 1

model = tf.keras.Sequential()
model.add(tf.keras.layers.Embedding(vocab_size, 64))
model.add(tf.keras.layers.Bidirectional(tf.keras.layers.LSTM(64)))
for units in [64, 64]:
    model.add(tf.keras.layers.Dense(units, activation='relu'))

# Output layer. The first argument is the number of labels.
model.add(tf.keras.layers.Dense(3, activation='softmax'))

model.compile(optimizer='adam',
              loss='sparse_categorical_crossentropy',
              metrics=['accuracy'])

model.summary()


print(' =============== train_data ==============')
print(train_data)
for tr1, _ in train_data.take(1):
    print('== train_data[1]')
    print(tr1)
    print(_)

print(' =============== test_data ==============')
print(test_data)
for test_1, _test_2 in test_data.take(1):
    print('== test_data[1]')
    print(test_1)
    print(_test_2)

print(' =============== all_encoded_data ==============')
print(all_encoded_data)
for a1, _ in all_encoded_data.take(1):
    print('== all_encoded_data[1]')
    print(a1)
    print(_)

# model.fit(train_data, epochs=3, validation_data=test_data)
