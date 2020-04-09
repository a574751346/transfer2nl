import nltk
from nltk.translate.bleu_score import SmoothingFunction

def nltk_sentence_bleu(hypothesis, reference, order=4):
    cc = SmoothingFunction()
    return nltk.translate.bleu([reference], hypothesis, smoothing_function=cc.method4)


def nltk_corpus_bleu(hypotheses, references, order=4):
    refs = []
    count = 0
    total_score1 = 0.0
    total_score2 = 0.0
    total_score3 = 0.0
    total_score4 = 0.0
    total_score = 0.0

    cc = SmoothingFunction()

    for hyp, ref in zip(hypotheses, references):
        hyp = hyp.split()
        ref = ref.split()
        refs.append([ref])

        try:
            score1 = nltk.translate.bleu([ref], hyp, smoothing_function=cc.method4, weights=(1,0,0,0))
            score2 = nltk.translate.bleu([ref], hyp, smoothing_function=cc.method4, weights=(0,1,0,0))
            score3 = nltk.translate.bleu([ref], hyp, smoothing_function=cc.method4, weights=(0,0,1,0))
            score4 = nltk.translate.bleu([ref], hyp, smoothing_function=cc.method4, weights=(0,0,0,1))
            score = nltk.translate.bleu([ref], hyp, smoothing_function=cc.method4)
        except ZeroDivisionError:
            print("##############################################")
            print("#########This is a ZeroDivisionError##########")
            print("##############################################")
            continue
        else:
            total_score1 += score1
            total_score2 += score2
            total_score3 += score3
            total_score4 += score4
            total_score += score
            count += 1

    avg_score1 = total_score1 / count
    avg_score2 = total_score2 / count
    avg_score3 = total_score3 / count
    avg_score4 = total_score4 / count
    avg_score = total_score / count
    corpus_bleu = nltk.translate.bleu_score.corpus_bleu(refs, hypotheses)
    print('corpus_bleu: %.4f avg_score: %.4f' % (corpus_bleu, avg_score))
    with open("score.txt", "a+") as f:
        f.write("{}\t{}\t{}\t{}\t{}\n".format(avg_score1,avg_score2,avg_score3,avg_score4,avg_score))


    return corpus_bleu, avg_score
