from common.word_vectorizer.wordVectorizer import WordVectorizer
from common.vocab import Vocab
import torch
import os
import numpy as np
import ujson as json


class Glove(WordVectorizer):
    def __init__(self, dataset, glove_path, emb_path):
        super(Glove, self).__init__(dataset)
        if os.path.isfile(emb_path):
            self.emb = torch.load(emb_path)
            self.word_size = self.emb.size(1)
        else:
            self.glove_vocab, self.vectors = self.load_word_vectors(glove_path)
            self.word_size = self.vectors.size(1)

            self.emb = torch.Tensor(dataset.vocab.size(), self.vectors.size(1)).normal_(-0.05, 0.05)
            for word in dataset.vocab.labelToIdx.keys():
                if self.glove_vocab.getIndex(word):
                    self.emb[dataset.vocab.getIndex(word)] = self.vectors[self.glove_vocab.getIndex(word)]
            self.emb[dataset.vocab.getIndex('')] = torch.zeros([self.word_size])
            torch.save(self.emb, emb_path)

        if torch.cuda.is_available():
            self.emb = self.emb.cuda()

    def load_word_vectors(self, path):
        """
        loading GLOVE word vectors
            if .pth file is found, will load that
            else will load from .txt file & save
        :param path:
        :return:
        """
        if os.path.isfile(path + '.pth') and os.path.isfile(path + '.vocab'):
            print('==> File found, loading to memory')
            vectors = torch.load(path + '.pth')
            vocab = Vocab(filename=path + '.vocab')
            return vocab, vectors
        # saved file not found, read from txt file
        # and create tensors for word vectors
        print('==> File not found, preparing, be patient')
        print(path + '.txt')
        count = sum(1 for line in open(path + '.txt', encoding="utf-8"))
        with open(path + '.txt', 'r') as f:
            contents = f.readline().rstrip('\n').split(' ')
            dim = len(contents[1:])
        words = [None] * (count)
        vectors = torch.zeros(count, dim)
        with open(path + '.txt', 'r', encoding="utf-8") as f:
            idx = 0
            for line in f:
                contents = line.rstrip('\n').split(' ')
                words[idx] = contents[0]
                vectors[idx] = torch.Tensor(list(map(float, contents[1:])))
                idx += 1
        with open(path + '.vocab', 'w', encoding="utf-8") as f:
            for word in words:
                f.write(word + '\n')
        vocab = Vocab(filename=path + '.vocab')
        torch.save(vectors, path + '.pth')
        return vocab, vectors

    def decode(self, word_seq):
        if word_seq in self.doc_idx:
            return self.embd[self.doc_idx[word_seq]]

        word_seq = word_seq.split()
        output = torch.Tensor(len(word_seq), self.word_size).normal_(-0.05, 0.05)
        for idx, word in enumerate(word_seq):
            if word in self.vocab.labelToIdx:
                output[idx] = self.vectors[self.vocab.labelToIdx[word]]

        return output
