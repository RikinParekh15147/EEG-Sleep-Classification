import unittest,sys,json,csv,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'gui/pipeline'))
from refinement import FEATURES,DOMAINS,sleep_architecture,refine_predictions,deviation_profile

class RefinementChecks(unittest.TestCase):
    def test_sleep_denominators_latency_terminal_wake_and_transitions(self):
        v=sleep_architecture([0,1,2,2,4,0,0])
        self.assertEqual(v['TST_minutes'],2)
        self.assertEqual(v['sleep_onset_latency_min'],.5)
        self.assertEqual(v['WASO_minutes'],1)
        self.assertEqual(v['REM_latency_min'],1.5)
        self.assertEqual(v['awakenings'],1)
        self.assertEqual(v['stage_transitions'],4)
        self.assertEqual(v['fragmentation_index'],120)
        self.assertEqual(sum(v[s+'_percent'] for s in ['N1','N2','N3','REM']),100)
    def test_missing_sleep_rem_and_continuity_do_not_create_normal_profiles(self):
        v=sleep_architecture([0,0]);self.assertIsNone(v['REM_latency_min']);self.assertIsNone(v['fragmentation_index']);self.assertIsNone(v['N1_percent'])
        self.assertIsNone(sleep_architecture([1,2])['REM_latency_min'])
        for kw in [{'timing_known':False},{'timestamps':[0,90]}]:
            v=sleep_architecture([1,0],**kw)
            for k in ['WASO_minutes','sleep_onset_latency_min','fragmentation_index','stage_transitions']:self.assertIsNone(v[k])
        self.assertEqual(deviation_profile(v,[])['sleep_health_deviation_profile'],'Unavailable')
    def test_percentile_boundary_equality_and_zero_sd(self):
        refs=[{'feature':k,'mean':10.,'std':0.,'p10':5.,'p90':15.} for k in {f for fs in DOMAINS.values() for f in fs}]
        vals={r['feature']:5. for r in refs};p=deviation_profile(vals,refs)
        self.assertEqual(p['sleep_health_deviation_profile'],'Within Reference');self.assertIsNone(p['deviations']['TST_minutes']['z'])
        vals['TST_minutes']=4.9;vals['WASO_minutes']=15.1;p=deviation_profile(vals,refs)
        self.assertEqual(p['deviated_domain_count'],2);self.assertEqual(p['sleep_health_deviation_profile'],'Moderate Deviation')
        vals['sleep_onset_latency_min']=None;self.assertEqual(deviation_profile(vals,refs)['sleep_health_deviation_profile'],'Unavailable')
    def test_all_verified_labels_and_architecture_match_desktop(self):
        d=ROOT/'refinement_artifacts/verified';model=json.loads((d/'refinement_model.json').read_text());profiles=json.loads((d/'subject_profiles.json').read_text())
        with (d/'test_epoch_predictions.csv').open() as f:rows=list(csv.DictReader(f))
        for sid in sorted({r['subject_id'] for r in rows}):
            sub=[r for r in rows if r['subject_id']==sid]
            expected=[int(r['refined_prediction']) for r in sub]
            self.assertEqual(refine_predictions([int(r['raw_prediction']) for r in sub],[[float(r[k]) for k in FEATURES] for r in sub],model),expected)
            for row in sub:
                if int(row['raw_prediction']) in [0,3,4]:self.assertEqual(row['raw_prediction'],row['refined_prediction'])
            p=next(p for p in profiles if p['subject_id']==sid and p['source']=='refined')
            for key,value in sleep_architecture(expected).items():
                self.assertTrue(value is None and p[key] is None or value is not None and math.isclose(value,p[key],abs_tol=1e-9),(sid,key))

if __name__=='__main__':unittest.main()
