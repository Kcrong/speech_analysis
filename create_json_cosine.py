from gensim.models import word2vec


def make_model2json(model_path):
    print("Loading model...")
    # model = word2vec.Word2Vec.load_word2vec_format(model_path, binary=True)  # C binary format
    model = word2vec.Word2Vec()
    model = model.load(model_path)
    print("Loading model: Done")

    # Name of output file
    f = open('web/data_cosine_skipgram.json', 'w')

    f.write("{\n")

    number_words = len(model.vocab)
    # number_words = 10000
    for i in range(0, number_words):
        stringA = list(model.vocab.items())[i][0]
        f.write("\n\"" + stringA + "\":[\n")

        nearest_words = model.most_similar(positive=[stringA], negative=[], topn=20)
        number_nearest_words = len(nearest_words)

        for j in range(0, number_nearest_words):
            f.write(
                "{\"w\":\"" + nearest_words[j][0] + "\",\"d\":" + str(round(nearest_words[j][1], 3)) + "}")
            if j != number_nearest_words - 1:
                f.write(",\n")
            else:
                f.write("]")

        if i != number_words - 1:
            f.write(",\n")
        else:
            f.write("\n")

    f.write("\n}\n")

    f.close()

    print("Finished!")

