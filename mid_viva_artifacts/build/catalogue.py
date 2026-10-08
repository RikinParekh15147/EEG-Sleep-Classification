from pathlib import Path
import json
rows=json.loads(Path('mid_viva_artifacts/build/ppt_inventory.json').read_text(encoding='utf-8'))
detail='Current detailed report: HMC split, preprocessing, model/uncertainty, spectral refinement, confusion matrices, gains, architecture equations, training references, four-domain profiles, dashboard, limitations and reproducibility.'
short='Current compact report: HMC input, model, nine spectral features, training/inference gates, gains, architecture, reference domains, recording profiles, dashboard, pipeline and limitations.'
mid='Mid-viva material: motivation, literature, data/epochs, preprocessing visuals, system diagram, model/training, refinement flowchart, gains, hypnogram/dashboard, proposed expert/temporal models and conclusion.'
descs={
'final_sleep_stage_project_presentation.pptx':detail,
'mid.original_backup.pptx':detail+' Updated third deck; its untouched original is under originals/.',
'sleep_stage_project_12_slides.pptx':short,
'EEG_Sleep_Mid_Viva_12_Slides_Reviewed.pptx':mid+' Reviewed light-background delivery.',
'EEG_Sleep_Mid_Viva_13_Slides.pptx':mid+' Light-background revision with stronger practical rationale and added stage/cycle explanation.',
'EEG_Sleep_Mid_Viva_Blue_15_Slides.pptx':mid+' First blue revision adds PDEU logo, four-part abstract and transparent team portraits. Superseded: chart labels needed contrast correction.',
'EEG_Sleep_Mid_Viva_Blue_15_Slides_Final.pptx':mid+' Blue revision with readable charts, logo, abstract and portraits ordered Om, Rikin, mentor.',
'EEG_Sleep_Mid_Viva_Blue_15_Slides_Mentor_First.pptx':mid+' Intermediate mentor-first revision. Superseded by the next file, which corrects a text-encoding artifact.',
'EEG_Sleep_Mid_Viva_Blue_15_Slides_Mentor_First_Final.pptx':mid+' LATEST MID-VIVA: blue, corrected chart labels, PDEU logo, Background/Method/Results/Future abstract; closing portraits Dr. Santosh, Om, Rikin.',
'candidate-blue15.pptx':mid+' Latest local blue 15-slide candidate including abstract/logo and mentor-first closing portraits.',
'candidate-13.pptx':mid+' Local 13-slide rationale/stages candidate.',
'candidate.pptx':mid+' Local initial 12-slide draft.',
'EEG_Sleep_Mid_Viva_12_Slides.pptx':mid+' Initial local 12-slide export, preceding the reviewed version.'
}
historical='Historical 3,773-epoch report: Transformer, training, uncertainty/calibration, Soft-Viterbi transitions, raw/smoothed results, heuristic profiles, future work and technical appendices. Superseded by current N1/N2 results.'
def describe(p):
    n=Path(p).name
    if p=='ppt_short_artifacts/source_copy.pptx':return historical+' Source copy for archived short-deck generation.'
    if p.startswith('refinement_artifacts/originals/'):
        if n=='mid.original_backup.pptx':return 'Untouched original progress/template deck: Transformer, uncertainty, Soft-Viterbi, biomarker/risk concepts, planned outputs and evidence placeholders. Not a completed verified report.'
        if n=='sleep_stage_project_12_slides.pptx':return 'Historical short deck: introduction, objectives, data/preprocessing, Transformer, raw/Soft-Viterbi results, uncertainty, SN009 sequence, heuristic profiles, future models, conclusion and literature.'
        return historical+' Preserved pre-update original.'
    if p.startswith('refinement_artifacts/build/'):return (short if '12_slides' in n else detail)+(' Local validated export of root deck.' if n.startswith('validated-') else ' Local pre-finalization build copy.')
    return descs[n]
table=['| PowerPoint path | Slides | Contents and status |','| --- | ---: | --- |']
for r in rows:table.append(f"| `{r['path']}` | {r['slides']} | {describe(r['path'])} |")
r=Path('README.md');s=r.read_text(encoding='utf-8').split('<!-- PPT_CATALOGUE -->')[0]
s+='<!-- PPT_CATALOGUE -->\n\n'+'\n'.join(table)+'\n\n'
s+='Temporary Office locks: `~$final_sleep_stage_project_presentation.pptx` and `~$sleep_stage_project_12_slides.pptx`. These are not decks and are excluded from Git.\n\n'
s+='### Latest mid-viva slide order\n\n1. Cover and PDEU logo\n2. Abstract: Background, Method, Results, Future Work\n3. Project purpose and rationale\n4. Stages and sleep cycles\n5. Literature review\n6. Dataset and EEG epochs\n7. Preprocessing\n8. System block diagram\n9. Model and training epochs\n10. Refinement flowchart\n11. Results and gains\n12. Hypnogram and GUI outputs\n13. Proposed multistage/multimodel architecture\n14. Conclusion and milestones\n15. Mentor and team: Dr. Santosh, Om, Rikin\n\nMatching PDFs accompany delivered root and mid-viva decks. Latest tables, charts and diagrams are editable; plots/screenshots are raster evidence. Portrait backgrounds were removed with imagegen; the supplied logo artwork was preserved. See [asset provenance](mid_viva_artifacts/assets/PROVENANCE.md).\n'
r.write_text(s,encoding='utf-8')
assert all('`'+x['path']+'`' in s for x in rows)
Path('mid_viva_artifacts/README.md').write_text('# Mid-viva presentations\n\nLatest: [mentor-first final 15-slide blue PowerPoint](output/EEG_Sleep_Mid_Viva_Blue_15_Slides_Mentor_First_Final.pptx) and [PDF](output/EEG_Sleep_Mid_Viva_Blue_15_Slides_Mentor_First_Final.pdf).\n\nThe deck includes the PDEU cover logo, four-part abstract, rationale and stages, literature, EEG epochs/preprocessing, editable architecture/flow diagrams and charts, verified gains, project outputs, proposed future models, conclusion, and transparent portraits ordered Dr. Santosh Sathpathy, Om Ahuja, Rikin Parekh.\n\nAll 15 slides were rendered with Microsoft PowerPoint. The closing slide was inspected after reordering; no text overflow was reported. The finalizer preserved original embedded chart workbooks and passed integrity, geometry, font, native-table and chart checks. Build with build/blue_revision/build_mentor_first.mjs; render with build/render_mentor_first.ps1.\n\nEarlier revisions remain in output/ and are documented individually in [the complete project README](../README.md#presentation-catalogue). Primary source: ../Biomarker_N1_N2_Refinement.ipynb; results: ../refinement_artifacts/verified/. The future architecture is proposed, not implemented.\n\nAsset source and editing details: [assets/PROVENANCE.md](assets/PROVENANCE.md). Temporary drafts, renders and validation files stay local; scripts and delivered artifacts are retained in Git.\n',encoding='utf-8')
print(f'Documented all {len(rows)} PowerPoints')
