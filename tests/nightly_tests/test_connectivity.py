#===============================================================================

import unittest

#===============================================================================

from mapknowledge import KnowledgeStore

#===============================================================================

from tests.config import Config

#===============================================================================

APINATOMY_MODEL = 'NeuronApinatComplex'

KEAST_BLADDER_MODEL = {
    'key-prefix': 'ilxtr:neuron-type-keast-',
    'paths': [
        {'id': 'ilxtr:neuron-type-keast-13',
         'models': 'ilxtr:neuron-type-keast-13'},
        {'id': 'ilxtr:neuron-type-keast-2',
         'models': 'ilxtr:neuron-type-keast-2'},
        {'id': 'ilxtr:neuron-type-keast-20',
         'models': 'ilxtr:neuron-type-keast-20'},
        {'id': 'ilxtr:neuron-type-keast-3',
         'models': 'ilxtr:neuron-type-keast-3'},
        {'id': 'ilxtr:neuron-type-keast-16',
         'models': 'ilxtr:neuron-type-keast-16'},
        {'id': 'ilxtr:neuron-type-keast-1',
         'models': 'ilxtr:neuron-type-keast-1'},
        {'id': 'ilxtr:neuron-type-keast-8',
         'models': 'ilxtr:neuron-type-keast-8'},
        {'id': 'ilxtr:neuron-type-keast-7',
         'models': 'ilxtr:neuron-type-keast-7'},
        {'id': 'ilxtr:neuron-type-keast-12',
         'models': 'ilxtr:neuron-type-keast-12'},
        {'id': 'ilxtr:neuron-type-keast-10',
         'models': 'ilxtr:neuron-type-keast-10'},
        {'id': 'ilxtr:neuron-type-keast-11',
         'models': 'ilxtr:neuron-type-keast-11'},
        {'id': 'ilxtr:neuron-type-keast-4',
         'models': 'ilxtr:neuron-type-keast-4'},
        {'id': 'ilxtr:neuron-type-keast-17',
         'models': 'ilxtr:neuron-type-keast-17'},
        {'id': 'ilxtr:neuron-type-keast-5',
         'models': 'ilxtr:neuron-type-keast-5'},
        {'id': 'ilxtr:neuron-type-keast-9',
         'models': 'ilxtr:neuron-type-keast-9'},
        {'id': 'ilxtr:neuron-type-keast-18',
         'models': 'ilxtr:neuron-type-keast-18'},
        {'id': 'ilxtr:neuron-type-keast-6',
         'models': 'ilxtr:neuron-type-keast-6'},
        {'id': 'ilxtr:neuron-type-keast-19',
         'models': 'ilxtr:neuron-type-keast-19'},
        {'id': 'ilxtr:neuron-type-keast-15',
         'models': 'ilxtr:neuron-type-keast-15'},
        {'id': 'ilxtr:neuron-type-keast-14',
         'models': 'ilxtr:neuron-type-keast-14'}
    ]
}

KEAST_NEURON_PATH_5 = {
    'id': 'ilxtr:neuron-type-keast-5',
    'label': 'neuron type kblad 5',
    'long-label': 'L6-S1 spinal cord (rexed laminae VII) to pelvic ganglion via white matter of L6-S1 via ventral root of L6-S1 via pelvic splanchnic nerve',
    'phenotypes': [
        'ilxtr:neuron-phenotype-para-pre'
    ],
    'taxons': [
        'NCBITaxon:10116'
    ],
    'connectivity': [
        (('ILX:0793615', ()), ('UBERON:0018675', ())),
        (('UBERON:0016578', ('ILX:0738432',)), ('ILX:0738432', ())),
        (('UBERON:0018675', ()), ('UBERON:0016508', ())),
        (('UBERON:0016578', ('UBERON:0006460',)), ('UBERON:0006460', ())),
        (('UBERON:0006460', ()), ('ILX:0792853', ())),
        (('ILX:0792853', ()), ('UBERON:0018675', ())),
        (('ILX:0738432', ()), ('ILX:0793615', ()))
    ],
    'references': [
        'http://www.ncbi.nlm.nih.gov/pubmed/12401325',
        'http://www.ncbi.nlm.nih.gov/pubmed/86176',
        'http://www.ncbi.nlm.nih.gov/pubmed/10473279',
        'http://www.ncbi.nlm.nih.gov/pubmed/9442414',
        'http://www.ncbi.nlm.nih.gov/pubmed/21283532',
        'http://www.ncbi.nlm.nih.gov/pubmed/7174880',
        'http://www.ncbi.nlm.nih.gov/pubmed/6736301'
    ],
    'expert-consultants': [
        'https://orcid.org/0000-0002-4341-3265'
    ],
    'forward-connections': [
        'ilxtr:neuron-type-keast-1'
    ],
    'node-phenotypes': {
        'ilxtr:hasSomaLocatedIn': [
            ('UBERON:0016578', ('UBERON:0006460',)),
            ('UBERON:0016578', ('ILX:0738432',))
        ],
        'ilxtr:hasAxonPresynapticElementIn': [
            ('UBERON:0016508', ())
        ],
        'ilxtr:hasAxonSensorySubcellularElementIn': [],
        'ilxtr:hasAxonLeadingToSensorySubcellularElementIn': [],
        'ilxtr:hasAxonLocatedIn': [
            ('ILX:0793615', ()),
            ('ILX:0792853', ()),
            ('UBERON:0018675', ())
        ],
        'ilxtr:hasDendriteLocatedIn': []
    },
    'nerves': [
        ('UBERON:0018675', ())
    ],
    'errors': []
}

#===============================================================================

class ConnectivityTestCase(unittest.TestCase):
    def __init__(self, *args, **kwds):
        super().__init__(*args, **kwds)
        self.__knowledge_store = KnowledgeStore(
            clean_connectivity=True,
            scicrunch_key=Config.SCICRUNCH_API_KEY
        )

    def test_connectivity_neurons(self):
        knowledge = self.__knowledge_store.entity_knowledge(APINATOMY_MODEL)
        keast_paths = [path for path in knowledge.get('paths', []) if path.get('id', '').startswith(KEAST_BLADDER_MODEL['key-prefix'])]
        assert len(keast_paths)
        assert len(keast_paths) == 20, 'Wrong number of neuron paths for Keast bladder model'

    def test_connectivity_neuron_group(self):
        knowledge = self.__knowledge_store.entity_knowledge(KEAST_NEURON_PATH_5['id'])
        knowledge_node_phenotypes = knowledge.get('node-phenotypes', {})
        keast_node_phenotypes = KEAST_NEURON_PATH_5.get('node-phenotypes', {})
        assert len(knowledge)
        assert len(knowledge.get('connectivity', [])) == len(KEAST_NEURON_PATH_5['connectivity']), 'Incorrect number of nodes for Keast neuron path 5'
        assert set(knowledge_node_phenotypes.get('ilxtr:hasSomaLocatedIn', [])) == set(keast_node_phenotypes['ilxtr:hasSomaLocatedIn']), 'Incorrect hasSomaLocatedIn node phenotype set for Keast neuron path 5'
        assert set(knowledge_node_phenotypes.get('ilxtr:hasAxonPresynapticElementIn', [])) == set(keast_node_phenotypes['ilxtr:hasAxonPresynapticElementIn']), 'Incorrect hasAxonPresynapticElementIn node phenotype set for Keast neuron path 5'
        assert set(knowledge_node_phenotypes.get('ilxtr:hasAxonLocatedIn', [])) == set(keast_node_phenotypes['ilxtr:hasAxonLocatedIn']), 'Incorrect hasAxonLocatedIn node phenotype set for Keast neuron path 5'
        assert set(knowledge.get('phenotypes', [])) == set(KEAST_NEURON_PATH_5.get('phenotypes', []))
        assert set(knowledge.get('taxons', [])) == set(KEAST_NEURON_PATH_5.get('taxons', []))
        assert set(knowledge.get('expert-consultants', [])) == set(KEAST_NEURON_PATH_5.get('expert-consultants', []))
        assert set(knowledge.get('forward-connections', [])) == set(KEAST_NEURON_PATH_5.get('forward-connections', []))
        assert set(knowledge.get('nerves', [])) == set(KEAST_NEURON_PATH_5.get('nerves', []))
        assert len(knowledge.get('references', [])) > 5, 'Too few references for Keast neuron path 5'

#===============================================================================
