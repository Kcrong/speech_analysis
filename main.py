"""
Word2vec Visualization
https://github.com/pvthuy/word2vec-visualization

발표 끝나고 학습시킨 모델을 바탕으로 위 사이트 처럼 Visualization 시키는 것도 나쁘지 않을 듯

"""
import os
import random
import string

from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
import matplotlib

from numpy import cov, mat, mean, array
from numpy import linalg as lin

"""
mat : 기본 행렬
cov : 공분산 행렬
linalg : linear algebra 선형대수 모듈
mean : Average

"""

matplotlib.rc('font', family='NanumGothic')

from gensim.models import Word2Vec
from konlpy.tag import Mecab

from create_json_cosine import make_model2json

mecab = Mecab()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
TRAIN_DATA_PATH = os.path.join(BASE_DIR, 'train')


def randomkey(length):
    """
    :param length: 길이
    :return: 해당 길이 만큼의 랜덤 문자열
    :example: randomkey(4) = "dkfd"
    """
    return ''.join(random.choice(string.ascii_lowercase) for i in range(length))


class MakeSentence:
    def search(self, dirname, file_list=list()):
        """
        :param file_list: 저장된 모든 파일 리스트
        :param dirname: 경로
        :return: 해당 경로 속 모든 파일 리스트
        """

        try:
            filenames = os.listdir(dirname)
            for filename in filenames:
                full_filename = os.path.join(dirname, filename)
                if os.path.isdir(full_filename):
                    # 재귀 형식을 이용해 해당 경로의 하위경로 파일까지 긁어옴
                    self.search(full_filename, file_list)
                else:
                    file_list.append(full_filename)
        except PermissionError:
            pass

        return file_list

    def make_sentences(self):
        sentences = list()
        for train_file in self.all_files:
            with open(os.path.join(self.datapath, train_file), 'r') as fp:
                sentences += [mecab.nouns(line) for line in fp.readlines() if line != '\n']
        return sentences

    def make_vocab(self):
        all_vocab = list()

        for train_file in self.all_files:
            with open(os.path.join(self.datapath, train_file), 'r') as fp:
                all_vocab.append([pos[0] for pos in mecab.pos(fp.read()) if pos[1] in ['NNG', 'NNP']])

        return all_vocab

    def __init__(self, datapath):
        """
        :param datapath: 학습할 데이터가 있는 경로
        :return: 해당 경로에 있는 모든 파일의 학습 데이터
        """
        self.datapath = datapath
        self.all_files = self.search(datapath)
        self.sentences = self.make_sentences()
        self.vocab = self.make_vocab()

    def __len__(self):
        return len(self.sentences)

    def __getitem__(self, index):
        return self.sentences[index]

    def __repr__(self):
        return "TrainData: \n%s" % ("\n".join([str(sentence) for sentence in self.sentences]))

    def __add__(self, other):
        self.sentences += other.sentences
        return self


class TrainModel:
    def __init__(self, train_data, name=None):
        """
        :param train_data: TrainData object or saved model path
        :return: Trained Vector Model
        """

        self.model = Word2Vec(min_count=20, size=3)

        try:
            if name is None:
                self.name = train_data.datapath
            else:
                self.name = name

        except AttributeError:
            # train_data 가 path 로 왔을 경우.
            self.model.load(train_data)

        else:
            self.sentences = train_data

            self.model.build_vocab(self.sentences.vocab)
            self.model.train(self.sentences)

        self.sorted_vocab = sorted(list(self.model.vocab.items()), key=lambda x: x[1].count, reverse=True)

    def most_similar(self, *args, **kwargs):
        """
        :param args, kwargs:
        :return:
        """
        return self.model.most_similar(*args, **kwargs)

    def save(self):
        """
        :return: moodel 이 저장된 경로
        """
        filename = randomkey(24)
        filepath = os.path.dirname(os.path.realpath(__file__))

        path = os.path.join(filepath, filename)

        self.model.save(path)

        return path

    def __len__(self):
        return len(self.sorted_vocab)

    def __getitem__(self, index):
        """
        :param index: list index
        :return: 해당 index 의 sorted_vocab data return.
        """
        return self.sorted_vocab[index]

    def __repr__(self):
        # return "<TrainModel %s...>" % (",".join([_vocab[0] for _vocab in self.sorted_vocab[:5]]))
        return "<TrainModel %s>" % self.name

    def __add__(self, other):
        """
        :param other: TrainModel 객체
        :return: 두 벡터를 합친 결과 (벡터)
        """

        # 우선 다시 학습을 시키는 방식으로 진행
        new_name = self.name + ' + ' + other.name
        new_model = TrainModel(self.sentences + other.sentences, new_name)

        return new_model

    def visualization_3d(self):

        def partition(alist, indices):
            # 해당 indices 의 리스트 를 반환
            return [mean(alist[i:j]) for i, j in zip([0] + indices, indices + [None])]

        vocab_list = list(self.model.vocab.keys())

        fig = plt.figure(figsize=(18, 13))
        ax = fig.gca(projection='3d')

        all_x = list()
        all_y = list()
        all_z = list()

        for vocab in vocab_list:
            # Need Dimensionality Reduction
            """
            # 100 차원 벡터를 행렬로 형변환
            # vocab_matrix = mat(self.model[vocab])

            # 고유값과 고유벡터 연산을 위한 공분산 행렬 구함
            cov_matrix = cov(self.model[vocab])

            from sklearn.manifold import TSNE

            tsne = TSNE(perplexity=30, n_components=2, init='pca', n_iter=5000)

            low_dim_embs = tsne.fit_transform()
            # labels = [word_dict[i] for i in range(len(self.model))]
            labels = list(self.model.vocab.keys())
            plot_with_labels(low_dim_embs, labels)
            """

            # vector = self.model[vocab]
            # ave_index = len(vector) // 3

            """
            x = mean(vector[:ave_index])
            y = mean(vector[ave_index:ave_index * 2])
            z = mean(vector[ave_index * 2:])
            """
            # x, y, z = partition(vector, [ave_index, ave_index*2])

            x, y, z = self.model[vocab]

            all_x.append(x)
            all_y.append(y)
            all_z.append(z)
            ax.text(x, y, z, vocab)

        ax.set_xlim3d(min(all_x), max(all_x))
        ax.set_ylim3d(min(all_y), max(all_y))
        ax.set_zlim3d(min(all_z), max(all_z))

        plt.show()

    def visualization_2d(self):
        # TODO: Here is Error
        vocab_list = list(self.model.vocab.keys())

        fig = plt.figure()
        ax = fig.gca(projection='2d')

        all_x = list()
        all_y = list()

        for vocab in vocab_list:
            x, y = self.model[vocab]
            all_x.append(x)
            all_y.append(y)
            ax.text(x, y, vocab)

        ax.set_xlim3d(min(all_x), max(all_x))
        ax.set_ylim3d(min(all_y), max(all_y))

        plt.show()

    # Just ShortCut
    visualization = visualization_3d


if __name__ == '__main__':
    park_sentences = MakeSentence(TRAIN_DATA_PATH + '/park')

    vector_model = TrainModel(park_sentences)

    vector_model.visualization()

    print(1)

    #    model_path = vector_model.save()

    #    make_model2json(model_path)

    """
    # 아래와 같이 model 끼리 덧셈도 가능하다.
    vector_model1 = TrainModel(sentences1)
    vector_model2 = TrainModel(sentences2)

    vector_model = vector_model1 + vector_model2

    for vocab in vector_model:
        print("%s : %d times" % (vocab[0], vocab[1].count))
    """
