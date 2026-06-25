import React from 'react';

interface ScaleMetrics {
  budget_allocated?: string;
  faculty_count?: string;
  support_staff_count?: string;
  beneficiary_capacity?: string;
}

interface Data {
  _id: string; // Adjusted to match the plain string ID in the JSON
  organization: string;
  fabric_of_accountability: string;
  human_and_financial_scale_context: string;
  scale_metrics?: ScaleMetrics;
  transparency_gap_introduction: string;
  missing_accountability_metrics: string[];
  transparency_gap_conclusion: string;
  citizen_action_item: string;
  created_at: string;
  updated_at: string;
}

// Pure helper function to handle lists safely
const RenderListItems = ({ items }: { items: string[] | undefined }) => {
  if (!items || items.length === 0) {
    return <p className="text-sm text-slate-400 italic">No information available.</p>;
  }

  return (
    <ul className="space-y-1.5 list-disc list-inside text-sm text-slate-300">
      {items.map((item, index) => (
        <li key={index} className="leading-relaxed">
          <span className="text-slate-200">{item}</span>
        </li>
      ))}
    </ul>
  );
};

const InfoCard = ( Data: Data) => {
  const data = Data?.Data;
  console.log("data from info card", data);

  if (!data) {
    return (
      <div className="p-6 text-center font-mono text-sm tracking-wider border border-red-900 bg-red-950/20 text-red-400 rounded-lg">
        DATA NOT AVAILABLE
      </div>
    );
  }

  const scaleMetrics = data.scale_metrics;

  return (
    <div className="max-w-4xl mx-auto my-6 overflow-hidden rounded-xl border border-slate-800 bg-slate-900/50 p-6 shadow-xl backdrop-blur-sm text-slate-100">
      
      {/* Header Section */}
      <div className="border-b border-slate-800 pb-4 mb-6">
        <span className="text-xs font-bold uppercase tracking-widest text-blue-400">Organization</span>
        <h2 className="text-2xl font-extrabold tracking-tight text-white mt-1 capitalize">{data.organization}</h2>
      </div>

      {/* Fabric & Context Section */}
      <div className="space-y-4 mb-8 bg-slate-950/40 p-4 rounded-lg border border-slate-800/60">
        <div>
          <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">Fabric of Accountability</h4>
          <p className="text-sm leading-relaxed text-slate-200">{data.fabric_of_accountability}</p>
        </div>
        <div>
          <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">Scale Context</h4>
          <p className="text-sm leading-relaxed text-slate-200">{data.human_and_financial_scale_context}</p>
        </div>
      </div>

      {/* Human and Financial Scale Metrics Grid */}
      <div className="mb-8">
        <h3 className="text-base font-bold text-white mb-3 flex items-center gap-2">
          <span className="h-2 w-2 rounded-full bg-blue-500"></span>
          Human &amp; Financial Scale Metrics
        </h3>
        {scaleMetrics ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 bg-slate-900 p-4 rounded-lg border border-slate-800">
            {scaleMetrics.budget_allocated && (
              <div className="text-sm">
                <span className="text-slate-400 block text-xs font-medium">Budget Allocated</span>
                <span className="text-emerald-400 font-semibold">{scaleMetrics.budget_allocated}</span>
              </div>
            )}
            {scaleMetrics.faculty_count && (
              <div className="text-sm">
                <span className="text-slate-400 block text-xs font-medium">Faculty Count</span>
                <span className="text-white font-semibold">{scaleMetrics.faculty_count}</span>
              </div>
            )}
            {scaleMetrics.support_staff_count && (
              <div className="text-sm">
                <span className="text-slate-400 block text-xs font-medium">Support Staff Count</span>
                <span className="text-white font-semibold">{scaleMetrics.support_staff_count}</span>
              </div>
            )}
            {scaleMetrics.beneficiary_capacity && (
              <div className="text-sm">
                <span className="text-slate-400 block text-xs font-medium">Beneficiary Capacity</span>
                <span className="text-white font-semibold">{scaleMetrics.beneficiary_capacity}</span>
              </div>
            )}
          </div>
        ) : (
          <p className="text-sm text-slate-400 italic">No Scale Metrics available.</p>
        )}
      </div>

      {/* Transparency Gaps & Missing Metrics */}
      <div className="mb-8 space-y-4">
        <div className="border-l-2 border-amber-500 pl-4 py-1">
          <h3 className="text-sm font-bold text-amber-400 uppercase tracking-wider mb-1">Transparency Gap Analysis</h3>
          <p className="text-sm text-slate-300 leading-relaxed">{data.transparency_gap_introduction}</p>
        </div>

        <div className="bg-slate-950/20 border border-slate-800/80 p-4 rounded-lg">
          <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Missing Accountability Metrics</h4>
          <RenderListItems items={data.missing_accountability_metrics} />
        </div>

        <p className="text-sm text-slate-400 italic leading-relaxed">{data.transparency_gap_conclusion}</p>
      </div>

      {/* Citizen Action Item */}
      <div className="p-4 bg-emerald-950/10 border border-emerald-900/50 rounded-lg">
        <h3 className="text-sm font-bold text-emerald-400 uppercase tracking-wider mb-2">Citizen Action Item</h3>
        <p className="text-sm leading-relaxed text-slate-200">{data.citizen_action_item}</p>
      </div>
      
    </div>
  );
};

export default InfoCard;