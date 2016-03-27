"""
Word2vec Visualization
https://github.com/pvthuy/word2vec-visualization

발표 끝나고 학습시킨 모델을 바탕으로 위 사이트 처럼 Visualization 시키는 것도 나쁘지 않을 듯

"""
import os
import random
import string

from gensim.models import Word2Vec
from konlpy.tag import Mecab

from create_json_cosine import make_model2json

mecab = Mecab()

TRAIN_DATA_PATH = '/home/kcrong/project/speech_nlp/train'


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

    def __init__(self, datapath):
        """
        :param datapath: 학습할 데이터가 있는 경로
        :return: 해당 경로에 있는 모든 파일의 학습 데이터
        """
        self.datapath = datapath
        self.all_files = self.search(datapath)
        self.sentences = self.make_sentences()

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
        :param train_data: TrainData object
        :return: Trained Vector Model
        """
        if name is None:
            self.name = train_data.datapath
        else:
            self.name = name
        self.sentences = train_data
        self.model = Word2Vec(min_count=1)

        # What Can We Do?
        # 단어를 처음 Build 해놓고 학습시킬 경우, 그 단어들의 Vector 만 재계산.
        # --> 새로운 단어를 추가하지 않음.
        self.model.build_vocab(self.sentences)
        self.model.train(self.sentences)
        self.sorted_vocab = sorted(list(self.model.vocab.items()), key=lambda x: x[1].count, reverse=True)

    def most_similar(self, *args, **kwargs):
        return self.model.most_similar(*args, **kwargs)

    def save(self):
        filename = randomkey(24)
        filepath = os.path.dirname(os.path.realpath(__file__))

        path = filepath + filename

        self.model.save(path)

        return path

    def __len__(self):
        return len(self.sorted_vocab)

    def __getitem__(self, index):
        return self.sorted_vocab[index]

    def __repr__(self):
        # return "<TrainModel %s...>" % (",".join([_vocab[0] for _vocab in self.sorted_vocab[:5]]))
        return "<TrainModel %s>" % self.name

    def __add__(self, other):
        """
        :param other: TrainModel 객체
        :return: 두 벡터를 합친 결과 (벡터)
        """

        """
        # TODO: 이게 왜 동작이 안되는지 모르겠다
        filename = 'tmp'
        other.model.save(filename)
        self.model.load(filename)
        """

        # 우선 다시 학습을 시키는 방식으로 진행
        new_name = self.name + ' + ' + other.name
        new_model = TrainModel(self.sentences + other.sentences, new_name)

        return new_model


if __name__ == '__main__':
    park_sentences = MakeSentence(TRAIN_DATA_PATH + '/park')

    vector_model = TrainModel(park_sentences)

    model_path = vector_model.save()

    make_model2json(model_path)

    """
    # 아래와 같이 model 끼리 덧셈도 가능하다.
    vector_model1 = TrainModel(sentences1)
    vector_model2 = TrainModel(sentences2)

    vector_model = vector_model1 + vector_model2

    for vocab in vector_model:
        print("%s : %d times" % (vocab[0], vocab[1].count))
    """
