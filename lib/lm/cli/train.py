from __future__ import print_function
import tensorflow as tf
import numpy as np
from lib.ds import Dataset, Vocabulary
from lib.cv import FeatureCache
from lib.sc import EmbeddingCache
import lib.lm as lm
import lib.etc as etc
import sys
import os

def lm_train():
    max_length = 30

    dataset = Dataset()

    vocabulary     = Vocabulary().restore("data/ds/vocabulary.csv")
    embedding_size = len(vocabulary)
    feature_size   = 512 + 1536

    reader = lm.SentenceReader("data/lm/training.csv",
                               embedding_size = embedding_size)

    batch_size = 128
    epochs     = 5000

    # Network Parameters
    num_hidden = 512 # hidden layer num of features

    model = lm.LanguageModel(max_length     = max_length,
                             embedding_size = embedding_size,
                             feature_size   = feature_size,
                             num_hidden     = num_hidden,
                             num_classes    = 200)

    init = tf.global_variables_initializer()

    embedding_cache = EmbeddingCache()
    embedding_cache.restore("data/sc/embeddings.csv")

    feature_cache = FeatureCache()
    feature_cache.restore("data/cv/features.csv")

    try:
        os.makedirs("logs")
    except:
        pass

    writer = tf.summary.FileWriter("logs", graph = tf.get_default_graph())

    sc_path = "pretrained/sc/SentenceClassifier"

    with tf.Session() as sess:
        sess.run(init)

        model.sentence_classifier.restore(sess, sc_path)

        print("Restored")

        for step, pi in etc.range(epochs):
            # Get a batch of training instances.
            instances, labels, sentences, lengths = \
            reader.read(lines = batch_size)

            features = [
                feature_cache.get(index)
                for index in instances
            ]

            features = [
                np.concatenate([ embedding_cache.get(label), feature ])
                for label, feature in features
            ]


            # Run optimization op (backprop)
            summary = model.train(sess, sentences, features, labels, lengths)
            writer.add_summary(summary, step)

            # Calculate batch accuracy and loss
            acc, loss, rel, dis = model.evaluate(sess, sentences, features,
                                                 labels, lengths)

            print("Iter " + str(1 + step) + " / " + str(epochs) + \
                  ", Minibatch Loss= " + \
                  "{:.6f}".format(loss) + \
                  " (rel: {:.6f}, dis: {:.6f})".format(rel, dis) + \
                  ", Training Accuracy= " + \
                  "{:.5f}".format(acc) + ", Time Remaining= " + \
                  etc.format_seconds(pi.time_remaining()), file = sys.stderr)

            # Generate a sample sentence after each 10 iterations.
            if (1 + step) % 10 == 0:
                sentences = model.generate(sess, features)

                for sentence in sentences[0 : 1]:
                    print(vocabulary.sentence([
                        word for word in sentence
                    ]), file = sys.stderr)

                model.save(sess, step)

        print("Optimization Finished!", file = sys.stderr)
