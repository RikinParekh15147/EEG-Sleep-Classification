import csv
import io
import json
import math
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'gui/pipeline'))
from core import STAGES,biomarkers,boundaries,calibration,classification,evidence_distribution,risk_profile,viterbi

class VerifiedPipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        p=ROOT/'ppt_artifacts'
        cls.rows=list(csv.DictReader(io.StringIO((p/'test_epoch_predictions.csv').read_text())))
        cls.metrics=json.loads((p/'overall_metrics.json').read_text())
        cls.transition=json.loads((p/'transition_config.json').read_text())
        cls.matrix=[[float(r[n]) for n in STAGES] for r in csv.DictReader(io.StringIO((p/'transition_matrix.csv').read_text()))]
        cls.profiles=list(csv.DictReader(io.StringIO((p/'subject_biomarkers.csv').read_text())))
        cls.calibration=json.loads((p/'calibration_metrics.json').read_text())
    def test_evidence_probabilities_and_uncertainty_match_every_verified_epoch(self):
        for row in self.rows:
            p,u,alpha=evidence_distribution([float(row['evidence_'+n]) for n in STAGES])
            self.assertAlmostEqual(u,float(row['uncertainty']),places=12)
            for i,n in enumerate(STAGES):self.assertAlmostEqual(p[i],float(row['prob_'+n]),places=12)
    def test_decoder_reproduces_all_four_verified_sequences_exactly(self):
        for sid in dict.fromkeys(r['subject_id'] for r in self.rows):
            sub=[r for r in self.rows if r['subject_id']==sid]
            actual=viterbi([[float(r['prob_'+n]) for n in STAGES] for r in sub],self.transition['initial_probabilities'],self.matrix,.9,[float(r['timestamp_seconds']) for r in sub])
            self.assertEqual(actual,[int(r['soft_viterbi_prediction']) for r in sub])
    def test_all_raw_and_smoothed_metrics_match_verified_evaluation(self):
        for condition,column in [('raw','raw_prediction'),('soft_viterbi','soft_viterbi_prediction')]:
            actual,_,_=classification([int(r['true_label']) for r in self.rows],[int(r[column]) for r in self.rows])
            for key,value in actual.items():self.assertAlmostEqual(value,self.metrics[condition][key],places=12)
    def test_all_twelve_biomarker_profiles_match_verified_values(self):
        columns={'raw':'raw_prediction','soft_viterbi':'soft_viterbi_prediction','ground_truth':'true_label'}
        for profile in self.profiles:
            sub=[r for r in self.rows if r['subject_id']==profile['subject_id']]
            actual=biomarkers([int(r[columns[profile['source']]]) for r in sub],[float(r['timestamp_seconds']) for r in sub])
            for key,value in actual.items():self.assertAlmostEqual(value,float(profile[key]),places=10)
            self.assertEqual(risk_profile(actual)[0],profile['risk_category'])
    def test_calibration_and_error_auc_match_verified_values(self):
        actual,_,_=calibration([int(r['true_label']) for r in self.rows],[[float(r['prob_'+n]) for n in STAGES] for r in self.rows],[float(r['uncertainty']) for r in self.rows])
        for key in ['ECE_10_equal_width_bins','multiclass_brier_sum','negative_log_likelihood','error_detection_AUROC','AURC_discrete_mean']:
            self.assertAlmostEqual(actual[key],self.calibration[key],places=10)
    def test_gap_resets_decoder_and_excludes_fragmentation_transition(self):
        p=[[.1,.1,.6,.1,.1],[.6,.1,.1,.1,.1]];initial=[.2]*5;transition=[[.96 if i==j else .01 for j in range(5)] for i in range(5)]
        self.assertEqual(viterbi(p,initial,transition,.9,[0,90]),[2,0])
        self.assertEqual(biomarkers([2,0],[0,90])['SFI'],0)
        self.assertEqual(biomarkers([2,0],[0,30])['SFI'],120)
    def test_unknown_continuity_does_not_claim_waso_sfi_or_risk(self):
        value=biomarkers([2,0],timing_known=False)
        self.assertIsNone(value['WASO_Minutes']);self.assertIsNone(value['SFI']);self.assertEqual(risk_profile(value)[0],'Unclassified')
    def test_invalid_inputs_and_zero_sleep_are_handled(self):
        for evidence in [[0]*4,[math.nan]*5,[-1,0,0,0,0]]:
            with self.assertRaises(ValueError):evidence_distribution(evidence)
        with self.assertRaises(ValueError):boundaries([30,0],2)
        self.assertEqual(risk_profile(biomarkers([0,0]))[0],'Unclassified')

if __name__=='__main__':unittest.main()
