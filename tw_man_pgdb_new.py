import polyglotdb, re
from polyglotdb import CorpusContext
import polyglotdb.io as pgio
from polyglotdb.query.base.func import Count, Average
from polyglotdb.acoustics.formants.base import analyze_formant_points
from polyglotdb.acoustics.formants.refined import analyze_formant_points_refinement
from polyglotdb.io.parsers.speaker import DirectorySpeakerParser


####
#### import data
####

corpus_root = '/Users/sijiazhang/Documents/Term_1_2021/LING513/final_project/taiwanese_mandarin'
speaker_info = '/Users/sijiazhang/Documents/Term_1_2021/LING513/final_project/taiwanese_mandarin_demographic.csv'

# creating parser for corpus
parser = pgio.inspect_textgrid(corpus_root)
parser.name = "friendly textgrid parser"
parser.speaker_parser = DirectorySpeakerParser()
parser.annotation_tiers[2].type_property = True
print(parser.annotation_tiers)

# for verbose output during corpus import:
parser.call_back = print

## we reset the corpus in case it was previously imported and we
## want to reload it
#with CorpusContext('tw_man') as c:
#    c.reset()

#change the name of the corpus?
# parsing the corpus
with CorpusContext('tw_man') as c:
    c.load(parser, corpus_root)

# checking if everything is as it should be
# print speakers, files
with CorpusContext('tw_man') as c:
    print('Speakers:', c.speakers)
    print('Discourses:', c.discourses)
    
####
#### Basic enrichment
####

# print phone set (don't worry about the query for now!)
with CorpusContext('tw_man') as c:
    q = c.query_lexicon(c.lexicon_phone)
    q = q.order_by(c.lexicon_phone.label)
    q = q.columns(c.lexicon_phone.label.column_name('phone'))
    phone_results = q.all()
    print(phone_results)

# we define a few subsets that will be useful later on
# (1) all phones
phone_set = [x.values[0] for x in phone_results]

# (2) non-segmental phones (silence, noise);
# (some of these are not in this corpus, but
# may be in others - you probably won't need
# to edit this list for other corpora, because
# they have all of the usual non-speech suspects
# for MFA-style textgrids!)
non_speech_set = ['sp', 'spn', '<SIL>', 'sil', '<sil>']

# (3) vowels (manually defined, but you can often
# do this more easily and more reliably using regexes)
vowel_set = ['e', 'a', 'u', 'i', 'ii', 'o', 'ao', 'v', 'ei', 'ou', 'ai' ]


# we now enrich the corpus with these subsets
#tell it its a subset
print("Encoding subsets")
with CorpusContext('tw_man') as c:
    c.encode_pauses(non_speech_set)
    c.encode_type_subset('phone', vowel_set, 'vowel')

# we now enrich the corpus with 'utterances' (marked by
# pauses that are at least 150 ms long - you could change
# this!)
print("Encoding utterances")
with CorpusContext('tw_man') as c:
    c.encode_utterances(min_pause_length=0.15)

# we now enrich the corpus with syllables that have
# vowels as their nuclei
# (side note: I'm not sure how syllabic consonants are
# handled in the phone set we use for English... so
# we're just using vowels here!)
print("Encoding syllables")
with CorpusContext('tw_man') as c:
    c.encode_syllables(syllabic_label='vowel')

# we also encode syllable count per word, phone count
# per syllable, phone count per word, syllable count
# per utterance and word count per utterance
print("Encoding counts")
with CorpusContext('tw_man') as c:
    c.encode_count('word', 'syllable', 'num_syllables_word')
    c.encode_count('utterance', 'syllable', 'num_syllables_uttr')
    c.encode_count('syllable', 'phone', 'num_phones_syll')
    c.encode_count('word', 'phone', 'num_phones_word')
    c.encode_count('utterance', 'word', 'num_words_uttr')

# we can now encode the speech rate of utterances
# based on how many syllables they have
# (i.e. syllables / sec)
print("Encoding speech rate")
with CorpusContext('tw_man') as c:
    c.encode_rate('utterance', 'syllable', 'speech_rate')

# we enrich the corpus with speaker demographic info based on
# a csv file
print("Adding speaker info")
with CorpusContext('tw_man') as c:
    c.enrich_speakers_from_csv(speaker_info)


####
#### Acoustic enrichment
####

# now let's enrich the corpus with refined formant measurements
# (this is done a bit differently from what we did, and
# tries to use an iterated process to gradually build more
# reliable prototypes)


#encode intensity as acoustic track measurements
print("Encoding intensity")    
with CorpusContext('tw_man') as c:
    c.config.praat_path = "/Applications/Praat.app/Contents/MacOS/Praat"
    c.analyze_intensity()
    
#encode tone properties to syllable units??
#with CorpusContext('tw_man') as c:
    #c.encode_phone.tone_to_syllables()

####
#### Extracting data
####

        
#### Query
#query disyllabic words and creat a subset of words
with CorpusContext('tw_man') as c:
    #q = c.query_graph(c.word).filter(c.word.num_syllables_word == 2)
    #q.create_subset('disyllabic_words')
    #encode a property showing if a syllable is the first or the second in a disyllabic word
    q = c.query_graph(c.word)
    q = q.filter(c.word.syllable.end == c.word.end)
    q.set_properties(final=word.syllable.label)
    
  
with CorpusContext('tw_man') as c:
    #q = c.query_graph(c.word).filter(c.word.subset == 'disyllabic_words')    
    q = c.query_graph(c.word)
    q = q.filter(c.word.syllable.begin == c.word.begin)
    q.set_properties(syllposition='initial')
    #print(q.all())
    

#create a subset --- initial syllables ?    
    
#export data
with CorpusContext('tw_man') as c:
    q = c.query_graph(c.word)
    q = q.filter(c.word.num_syllables_word == 2)
    
    q = q.columns(
        c.word.speaker.name.column_name('speaker'),
        c.word.discourse.name.column_name('file'),
        c.word.id.column_name('word_id'),
        c.word.label.column_name('word'),
        )
    #q = q.filter(c.word.syllposition == 'initial')
    q = q.columns(
        #to know what syllables each word contain
        c.word.syllable.label.column_name('initial syllable'),
        c.word.syllable.syllposition.column_name('position_in_word'),
        c.word.syllable.begin.column_name('initial_syllable'), 
        c.syllable.end.column_name('final_syllable'),
        c.syllable.duration.column_name('syllable_duration'),
        c.syllable.phone.tones.column_name('syllable_tone'),
        c.syllable.intensity.mean.column_name('syllable_intensity')
        )
    results = q.all()
    print(results)
    q.to_csv('/Users/sijiazhang/Documents/Term_1_2021/LING513/final_project/tw_man_syllables_new.csv')
        
        