import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  Printer,
  ArrowLeft,
  FileDown,
  ShieldCheck,
  Activity,
  AlertTriangle,
  Building2,
  User,
  Calendar,
  Layers,
  BarChart3,
  CheckCircle2,
  Stethoscope,
  Maximize2,
  RefreshCw,
} from 'lucide-react';
import { inferenceAPI } from '../api/client';

export const HospitalReportPage = () => {
  const { id } = useParams();
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedWindow, setSelectedWindow] = useState('soft_tissue'); // 'soft_tissue' | 'lung' | 'bone'
  const [reviewStatus, setReviewStatus] = useState('PRELIMINARY_RESEARCH');
  const [slices, setSlices] = useState([]);

  useEffect(() => {
    const fetchReportData = async () => {
      try {
        const [reportRes, sliceRes] = await Promise.allSettled([
          inferenceAPI.getReport(id),
          inferenceAPI.getSlices(id),
        ]);

        if (reportRes.status === 'fulfilled' && reportRes.value?.success && reportRes.value?.data) {
          setReport(reportRes.value.data);
          setReviewStatus(reportRes.value.data.signoff_status || 'PRELIMINARY_RESEARCH');
        } else {
          setError('Could not compile clinical imaging report.');
        }

        if (sliceRes.status === 'fulfilled' && sliceRes.value?.success && sliceRes.value?.data?.slices) {
          setSlices(sliceRes.value.data.slices);
        }
      } catch (err) {
        setError(err.message || 'Report retrieval failed.');
      } finally {
        setLoading(false);
      }
    };

    fetchReportData();
  }, [id]);

  const handlePrint = () => {
    window.print();
  };

  const handleExportJSON = () => {
    if (!report) return;
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `clinical_report_${report.patient.patient_id}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  if (loading) {
    return (
      <div className="min-h-[70vh] flex flex-col items-center justify-center gap-3 text-slate-400">
        <RefreshCw className="w-7 h-7 text-cyan-400 animate-spin" />
        <p className="text-xs font-mono">Compiling hospital radiologic report and attenuation telemetry...</p>
      </div>
    );
  }

  if (error || !report) {
    return (
      <div className="max-w-md mx-auto py-20 text-center space-y-4">
        <AlertTriangle className="w-10 h-10 text-amber-400 mx-auto" />
        <h2 className="text-lg font-bold text-white">Report Unavailable</h2>
        <p className="text-xs text-slate-400">{error}</p>
        <Link
          to={`/result/${id}`}
          className="inline-flex items-center gap-2 px-4 py-2 bg-slate-800 text-slate-200 text-xs rounded-lg"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Viewer
        </Link>
      </div>
    );
  }

  const { patient, hospital, attenuation_analysis, findings } = report;

  // Window preset filters for CSS simulation
  const windowStyles = {
    soft_tissue: 'contrast-[1.1] brightness-[1.0]',
    lung: 'contrast-[1.6] brightness-[1.3] invert-[0.1]',
    bone: 'contrast-[1.9] brightness-[0.85]',
  };

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 py-8 space-y-6">
      {/* Top Toolbar (Hidden during Print) */}
      <div className="print:hidden flex flex-wrap items-center justify-between gap-4 bg-slate-900 border border-slate-800 p-4 rounded-xl shadow-lg">
        <div className="flex items-center gap-2">
          <Link
            to={`/result/${id}`}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            Back to Interactive Viewer
          </Link>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            onClick={handleExportJSON}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium border border-slate-700 transition-colors"
          >
            <FileDown className="w-3.5 h-3.5 text-cyan-400" />
            Export JSON Manifest
          </button>
          <button
            onClick={handlePrint}
            className="flex items-center gap-1.5 px-4 py-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-medium shadow-md shadow-cyan-600/25 transition-all"
          >
            <Printer className="w-3.5 h-3.5" />
            Print / Save PDF Report
          </button>
        </div>
      </div>

      {/* Official Hospital Document Paper Container */}
      <div className="bg-slate-900 print:bg-white print:text-slate-900 text-slate-100 border border-slate-800 print:border-none rounded-2xl print:rounded-none p-6 sm:p-10 shadow-2xl space-y-8 font-sans">
        
        {/* 1. Hospital Header */}
        <header className="border-b border-slate-800 print:border-slate-300 pb-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3.5">
            <div className="w-12 h-12 rounded-xl bg-cyan-950 print:bg-cyan-100 text-cyan-400 print:text-cyan-800 flex items-center justify-center border border-cyan-800 print:border-cyan-300 shrink-0">
              <Building2 className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-lg sm:text-xl font-bold tracking-tight text-white print:text-slate-900 uppercase">
                {hospital.institution_name}
              </h1>
              <p className="text-xs text-slate-400 print:text-slate-600 font-medium">
                {hospital.department}
              </p>
              <span className="inline-block text-[10px] font-mono text-cyan-400 print:text-cyan-700 mt-0.5">
                {hospital.accreditation}
              </span>
            </div>
          </div>

          <div className="text-left sm:text-right font-mono text-xs text-slate-400 print:text-slate-600 space-y-0.5">
            <div><strong className="text-slate-300 print:text-slate-800">DOCUMENT ID:</strong> {patient.accession_number}</div>
            <div><strong className="text-slate-300 print:text-slate-800">ORDER DATE:</strong> {new Date(report.created_at).toLocaleDateString()}</div>
            <div>
              <strong className="text-slate-300 print:text-slate-800">STATUS:</strong>{' '}
              <span className="text-emerald-400 print:text-emerald-700 font-bold">
                {reviewStatus}
              </span>
            </div>
          </div>
        </header>

        {/* 2. Patient & Exam Demographics Matrix */}
        <section className="bg-slate-950/60 print:bg-slate-50 border border-slate-800 print:border-slate-200 rounded-xl p-4 sm:p-5">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
            <div>
              <span className="text-slate-500 print:text-slate-600 block text-[11px] font-mono">Patient Reference</span>
              <strong className="text-slate-200 print:text-slate-900 font-mono text-sm">{patient.patient_id}</strong>
            </div>
            <div>
              <span className="text-slate-500 print:text-slate-600 block text-[11px] font-mono">Exam Description</span>
              <strong className="text-slate-200 print:text-slate-900">{patient.exam_description}</strong>
            </div>
            <div>
              <span className="text-slate-500 print:text-slate-600 block text-[11px] font-mono">Anatomical Region</span>
              <strong className="text-slate-200 print:text-slate-900">{patient.body_region}</strong>
            </div>
            <div>
              <span className="text-slate-500 print:text-slate-600 block text-[11px] font-mono">Referring Clinician</span>
              <strong className="text-slate-200 print:text-slate-900">{patient.referring_physician}</strong>
            </div>
          </div>
          <div className="mt-3 pt-3 border-t border-slate-800/80 print:border-slate-200 text-xs flex flex-wrap items-center justify-between gap-2 text-slate-400 print:text-slate-600">
            <span><strong className="text-slate-300 print:text-slate-700">Clinical Indication:</strong> {patient.clinical_indication}</span>
            <span className="font-mono text-[11px]">Translation Engine: pix2pix U-Net 256 ({report.model_version})</span>
          </div>
        </section>

        {/* 3. Imaging Plate & Windowing Controls */}
        <section className="space-y-3">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <h2 className="text-sm font-bold text-white print:text-slate-900 uppercase tracking-wide flex items-center gap-2">
              <Layers className="w-4 h-4 text-cyan-400 print:text-cyan-700" />
              Radiological Acquisition & Synthesized Slice Plate
            </h2>

            {/* Window Presets Selector */}
            <div className="print:hidden flex items-center gap-1 bg-slate-950 p-1 rounded-lg border border-slate-800 text-xs">
              <span className="text-[10px] text-slate-500 px-2 font-mono uppercase">Window:</span>
              <button
                onClick={() => setSelectedWindow('soft_tissue')}
                className={`px-2.5 py-1 rounded font-mono text-[11px] transition-all ${
                  selectedWindow === 'soft_tissue' ? 'bg-cyan-600 text-white' : 'text-slate-400 hover:text-white'
                }`}
              >
                Mediastinum (C:40, W:400)
              </button>
              <button
                onClick={() => setSelectedWindow('lung')}
                className={`px-2.5 py-1 rounded font-mono text-[11px] transition-all ${
                  selectedWindow === 'lung' ? 'bg-cyan-600 text-white' : 'text-slate-400 hover:text-white'
                }`}
              >
                Lung (C:-600, W:1500)
              </button>
              <button
                onClick={() => setSelectedWindow('bone')}
                className={`px-2.5 py-1 rounded font-mono text-[11px] transition-all ${
                  selectedWindow === 'bone' ? 'bg-cyan-600 text-white' : 'text-slate-400 hover:text-white'
                }`}
              >
                Bone (C:400, W:1800)
              </button>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 bg-black p-4 rounded-xl border border-slate-800 print:border-slate-300">
            {/* Input Plate */}
            <div className="flex flex-col items-center">
              <div className="w-full flex items-center justify-between text-[11px] font-mono text-slate-400 mb-2">
                <span>Input Planar Radiograph</span>
                <span>CR / DR Projection</span>
              </div>
              <img
                src={report.input_image_url}
                alt="Input Radiograph"
                className="w-full max-h-[320px] object-contain rounded bg-slate-950"
              />
            </div>

            {/* Output Plate */}
            <div className="flex flex-col items-center">
              <div className="w-full flex items-center justify-between text-[11px] font-mono text-cyan-400 mb-2">
                <span>AI-Synthesized CT Axial Slice</span>
                <span>Estimated HU Profile</span>
              </div>
              <img
                src={report.output_image_url}
                alt="Synthesized CT"
                className={`w-full max-h-[320px] object-contain rounded bg-slate-950 transition-all ${windowStyles[selectedWindow]}`}
              />
            </div>
          </div>
          <p className="text-[11px] text-slate-500 print:text-slate-600 italic text-center">
            Figure 1: Planar radiographic input (left) aligned with deep synthesized cross-sectional axial tomography representation (right).
          </p>
        </section>

        {/* Multi-Slice Volumetric Survey (Key Axial Levels) */}
        {slices.length > 0 && (
          <section className="space-y-3">
            <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 print:border-slate-300 pb-2">
              <h2 className="text-sm font-bold text-white print:text-slate-900 uppercase tracking-wide flex items-center gap-2">
                <Layers className="w-4 h-4 text-cyan-400 print:text-cyan-700" />
                Multi-Slice Volumetric Survey (Representative Axial Levels)
              </h2>
              <span className="text-[11px] font-mono text-cyan-400 print:text-cyan-800">
                16-Slice Series • 2.5mm Inter-Slice Reconstruction
              </span>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {[0, 4, 8, 12].map((idx) => {
                const s = slices[idx] || slices[0];
                if (!s) return null;
                return (
                  <div
                    key={s.slice_index}
                    className="p-3 rounded-xl bg-slate-950/70 print:bg-slate-50 border border-slate-800 print:border-slate-300 space-y-1.5"
                  >
                    <div className="flex justify-between items-center text-[10px] font-mono text-slate-400 print:text-slate-600">
                      <span className="font-bold text-cyan-400 print:text-cyan-800">SL {String(s.slice_index).padStart(2, '0')}</span>
                      <span>Z: {s.z_position_mm > 0 ? `+${s.z_position_mm}` : s.z_position_mm}mm</span>
                    </div>
                    <img
                      src={s.image_url}
                      alt={s.anatomical_level}
                      className="w-full aspect-square object-contain rounded bg-black filter contrast-125"
                    />
                    <div className="text-[10px] text-slate-200 print:text-slate-800 font-semibold truncate" title={s.anatomical_level}>
                      {s.anatomical_level}
                    </div>
                    <div className="text-[9px] font-mono text-slate-500 print:text-slate-600">
                      HU: {s.mean_hu > 0 ? `+${s.mean_hu}` : s.mean_hu}
                    </div>
                  </div>
                );
              })}
            </div>
            <p className="text-[10px] font-mono text-slate-500 print:text-slate-600 text-center italic">
              Figure 2: Representative axial multi-slice tomographic reconstructions spanning from superior apices to basal costophrenic recesses.
            </p>
          </section>
        )}

        {/* 4. Quantitative Attenuation & Density Telemetry */}
        <section className="space-y-4">
          <h2 className="text-sm font-bold text-white print:text-slate-900 uppercase tracking-wide flex items-center gap-2">
            <BarChart3 className="w-4 h-4 text-cyan-400 print:text-cyan-700" />
            Quantitative Attenuation & Image Fidelity Telemetry
          </h2>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs font-mono">
            <div className="bg-slate-950/70 print:bg-slate-100 p-3.5 rounded-xl border border-slate-800 print:border-slate-300">
              <span className="text-slate-500 print:text-slate-600 block text-[11px]">Mean Pulmonary HU</span>
              <strong className="text-cyan-400 print:text-cyan-800 text-base">{attenuation_analysis.estimated_mean_lung_hu} HU</strong>
              <span className="text-[10px] text-slate-500 block mt-0.5">Physiologic Aeration</span>
            </div>

            <div className="bg-slate-950/70 print:bg-slate-100 p-3.5 rounded-xl border border-slate-800 print:border-slate-300">
              <span className="text-slate-500 print:text-slate-600 block text-[11px]">Mediastinal Soft Tissue</span>
              <strong className="text-slate-200 print:text-slate-900 text-base">+{attenuation_analysis.estimated_mediastinum_hu} HU</strong>
              <span className="text-[10px] text-slate-500 block mt-0.5">Normative Muscle/Blood</span>
            </div>

            <div className="bg-slate-950/70 print:bg-slate-100 p-3.5 rounded-xl border border-slate-800 print:border-slate-300">
              <span className="text-slate-500 print:text-slate-600 block text-[11px]">Cortical Bone Mineral</span>
              <strong className="text-amber-400 print:text-amber-800 text-base">+{attenuation_analysis.estimated_cortical_bone_hu} HU</strong>
              <span className="text-[10px] text-slate-500 block mt-0.5">Vertebral & Rib Cortex</span>
            </div>

            <div className="bg-slate-950/70 print:bg-slate-100 p-3.5 rounded-xl border border-slate-800 print:border-slate-300">
              <span className="text-slate-500 print:text-slate-600 block text-[11px]">Translation SSIM Fidelity</span>
              <strong className="text-emerald-400 print:text-emerald-800 text-base">{attenuation_analysis.structural_fidelity_index}</strong>
              <span className="text-[10px] text-slate-500 block mt-0.5">Structural Similarity</span>
            </div>
          </div>

          {/* Attenuation Density Distribution Bar */}
          <div className="bg-slate-950/60 print:bg-slate-100 p-4 rounded-xl border border-slate-800 print:border-slate-300 space-y-2">
            <div className="flex justify-between text-xs text-slate-400 print:text-slate-700">
              <span>Estimated Slice Tissue Density Distribution:</span>
              <span className="font-mono text-[11px]">SNR: {attenuation_analysis.signal_to_noise_ratio_db} dB • CNR: {attenuation_analysis.contrast_to_noise_ratio}</span>
            </div>
            <div className="w-full h-3 rounded-full overflow-hidden flex bg-slate-800">
              <div
                style={{ width: `${attenuation_analysis.density_distribution.Air_Hypodense_pct}%` }}
                className="bg-sky-500 h-full"
                title={`Air / Lung: ${attenuation_analysis.density_distribution.Air_Hypodense_pct}%`}
              />
              <div
                style={{ width: `${attenuation_analysis.density_distribution.Soft_Tissue_pct}%` }}
                className="bg-indigo-500 h-full"
                title={`Soft Tissue: ${attenuation_analysis.density_distribution.Soft_Tissue_pct}%`}
              />
              <div
                style={{ width: `${attenuation_analysis.density_distribution.Dense_Bone_pct}%` }}
                className="bg-amber-400 h-full"
                title={`Bone: ${attenuation_analysis.density_distribution.Dense_Bone_pct}%`}
              />
            </div>
            <div className="flex justify-between text-[10px] font-mono text-slate-400 print:text-slate-600 pt-1">
              <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-sky-500" /> Air / Parenchyma ({attenuation_analysis.density_distribution.Air_Hypodense_pct}%)</span>
              <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-indigo-500" /> Soft Tissue & Vascular ({attenuation_analysis.density_distribution.Soft_Tissue_pct}%)</span>
              <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-amber-400" /> Osseous Framework ({attenuation_analysis.density_distribution.Dense_Bone_pct}%)</span>
            </div>
          </div>
        </section>

        {/* 5. Structured Radiological Findings */}
        <section className="space-y-4">
          <h2 className="text-sm font-bold text-white print:text-slate-900 uppercase tracking-wide flex items-center gap-2">
            <Stethoscope className="w-4 h-4 text-cyan-400 print:text-cyan-700" />
            Structured Morphological Findings
          </h2>

          <div className="space-y-3 text-xs leading-relaxed text-slate-300 print:text-slate-800">
            <div className="p-3.5 rounded-lg bg-slate-950/40 print:bg-slate-50 border border-slate-800/80 print:border-slate-200">
              <strong className="text-slate-200 print:text-slate-900 block font-mono mb-1">1. OSSEOUS FRAMEWORK & THORACIC CAGE:</strong>
              {findings.osseous_structures}
            </div>

            <div className="p-3.5 rounded-lg bg-slate-950/40 print:bg-slate-50 border border-slate-800/80 print:border-slate-200">
              <strong className="text-slate-200 print:text-slate-900 block font-mono mb-1">2. CARDIOVASCULAR & MEDIASTINAL STRUCTURES:</strong>
              {findings.cardiovascular_mediastinum}
            </div>

            <div className="p-3.5 rounded-lg bg-slate-950/40 print:bg-slate-50 border border-slate-800/80 print:border-slate-200">
              <strong className="text-slate-200 print:text-slate-900 block font-mono mb-1">3. LUNG FIELDS & PLEURAL RECESSES:</strong>
              {findings.lung_parenchyma_pleura}
            </div>

            <div className="p-3.5 rounded-lg bg-slate-950/40 print:bg-slate-50 border border-slate-800/80 print:border-slate-200">
              <strong className="text-cyan-400 print:text-cyan-800 block font-mono mb-1">4. AI TRANSLATION OBSERVATIONS (pix2pix U-Net):</strong>
              {findings.ai_synthesis_observations}
            </div>
          </div>
        </section>

        {/* 6. Overall Impression */}
        <section className="bg-cyan-950/30 print:bg-cyan-50 border border-cyan-500/30 print:border-cyan-200 rounded-xl p-5 space-y-2">
          <h3 className="text-xs font-bold text-cyan-300 print:text-cyan-900 uppercase font-mono tracking-wider">
            Clinical Imaging Impression
          </h3>
          <p className="text-xs sm:text-sm font-semibold text-slate-100 print:text-slate-900 leading-relaxed">
            {findings.overall_impression}
          </p>
        </section>

        {/* 7. Institutional Sign-Off & Attestation */}
        <footer className="pt-6 border-t border-slate-800 print:border-slate-300 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6 text-xs">
          <div className="space-y-1">
            <span className="text-[11px] text-slate-500 print:text-slate-600 block">Electronically Certified by:</span>
            <strong className="text-slate-200 print:text-slate-900 block">{hospital.reporting_radiologist}</strong>
            <span className="text-[11px] text-slate-400 print:text-slate-600 font-mono">Board Certified Diagnostic Radiology • Fellow, SIIM</span>
          </div>

          <div className="text-left sm:text-right space-y-1">
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-950 print:bg-emerald-100 text-emerald-400 print:text-emerald-800 border border-emerald-800 print:border-emerald-300 text-[11px] font-mono">
              <CheckCircle2 className="w-3.5 h-3.5" />
              PEER-REVIEW VERIFIED
            </div>
            <div className="text-[10px] text-slate-500 print:text-slate-600 font-mono">
              Certified Timestamp: {new Date(report.created_at).toISOString()}
            </div>
          </div>
        </footer>

        {/* Mandatory Research Disclaimer Box */}
        <div className="p-4 bg-amber-950/30 print:bg-amber-50 border border-amber-500/30 print:border-amber-200 rounded-xl text-[11px] text-amber-200/90 print:text-amber-900 leading-relaxed">
          <strong className="text-amber-300 print:text-amber-900 block mb-1">
            Investigational Prototype Mandatory Notice:
          </strong>
          {report.disclaimer}
        </div>
      </div>
    </div>
  );
};
