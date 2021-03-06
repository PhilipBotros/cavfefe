from __future__ import print_function
import tensorflow as tf
import numpy as np
from lib.ds import Vocabulary
from lib.sc import SentenceClassifier, SentenceReader, EmbeddingCache
import lib.etc as etc
import sys
import progressbar

def sc_extract_embeddings():
    max_length     = 30
    num_classes    = 200
    embedding_size = len(Vocabulary().restore("data/ds/vocabulary.csv"))

    reader = SentenceReader("data/sc/training.csv",
                            num_classes, embedding_size = embedding_size)

    epochs     = num_classes

    # Network Parameters
    num_hidden = 512 # hidden layer num of features

    model = SentenceClassifier(max_length, embedding_size,
                               num_hidden, num_classes)

    init = tf.global_variables_initializer()

    cache = EmbeddingCache()

    with tf.Session() as sess:
        sess.run(init)

        model.restore(sess, "pretrained/sc/SentenceClassifier")

        for step, pi in etc.range(epochs):
            # Get a batch of training instances.
            batch_x, batch_y, batch_len = reader.query(label = step + 1)

            # Calculate batch accuracy and loss
            activations = model.extract(sess, batch_x, batch_y, batch_len)
            embedding   = np.mean(activations, axis = 0)

            cache.set(step + 1, embedding)

            print("Iter " + str(1 + step) + " / " + str(epochs) + \
                  ", Time Remaining= " + \
                  etc.format_seconds(pi.time_remaining()), file = sys.stderr)

    cache.save("data/sc/embeddings.csv")
