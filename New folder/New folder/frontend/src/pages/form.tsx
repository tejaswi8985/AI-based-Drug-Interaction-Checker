import { useEffect, useState } from 'react'
import axios from "axios";
import '../App.css'

const FLASK_URL = "http://127.0.0.1:5000";
const NODE_URL = "http://localhost:5001";

type ApiResponse = {
  message: any;
  status: string;
  ayurvedic_name: string;
  canonical_name: string;
  allopathic_drug_name: string;
  clinical_effect: string;
  interaction_severity: string;
  mechanism: string;
  recommendation: string;
  drug_class: string;
  therapeutic_category: string;
  evidence_text: string;
  user_entered_drug: string;
  source: string;
};

type InteractionItem = {
  ayurvedic_name: string;
  canonical_name: string;
  allopathic_drug_name: string;
  interaction_severity: string;
  mechanism: string;
  clinical_effect: string;
  recommendation: string;
  input_supplement: string;
  input_drug: string;
};

type NoInteractionItem = {
  supplement: string;
  drug: string;
  status: string;
};

type InteractionResult = {
  status: string;
  interactions: InteractionItem[];
  no_interactions: NoInteractionItem[];
  input_supplements: string[];
  total_pairs_checked: number;
  total_interactions_found: number;
};

function severityColor(severity: string): string {
  const s = severity?.toLowerCase();
  if (s === "danger" || s === "high" || s === "severe") return "#e53e3e";
  if (s === "moderate" || s === "medium") return "#dd6b20";
  if (s === "mild" || s === "low" || s === "safe") return "#38a169";
  return "#718096";
}

function SeverityBadge({ severity }: { severity: string }) {
  return (
    <span style={{
      backgroundColor: severityColor(severity),
      color: "white",
      padding: "2px 10px",
      borderRadius: "12px",
      fontSize: "11px",
      fontWeight: "bold",
      textTransform: "capitalize",
      whiteSpace: "nowrap"
    }}>
      {severity || "Unknown"}
    </span>
  );
}

function Form() {
  const [history, setHistory] = useState<string[]>([]);
  const [query, setQuery] = useState<string>("");
  const [result, setResult] = useState<ApiResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [userData, setUserData] = useState<any>(null);

  useEffect(() => {
    const email = localStorage.getItem("userEmail");
    if (!email) return;
    axios.get(`${NODE_URL}/api/user/${email}`)
      .then(res => setUserData(res.data))
      .catch(err => console.error("User fetch error:", err));
  }, []);

  useEffect(() => {
    const email = localStorage.getItem("userEmail");
    if (!email) return;
    axios.get(`${NODE_URL}/api/history/${email}`)
      .then(res => setHistory(res.data.history || []))
      .catch(err => console.error("History load error:", err));
  }, []);

  const fetchData = async (customQuery?: string) => {
    const searchQuery = (customQuery || query).trim().toLowerCase();
    const email = localStorage.getItem("userEmail");

    if (!searchQuery) { alert("Please enter a drug name"); return; }
    if (!email) { alert("You are not logged in. Please log in again."); return; }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const res = await axios.get<ApiResponse>(`${FLASK_URL}/api?q=${encodeURIComponent(searchQuery)}`);

      if (res.data.status === "not_found" || res.data.message?.includes("not available")) {
        setError(res.data.message);
        setLoading(false);
        return;
      }

      setResult(res.data);
      await axios.post(`${NODE_URL}/api/save-search`, { email, query: searchQuery });
      const historyRes = await axios.get(`${NODE_URL}/api/history/${email}`);
      setHistory(historyRes.data.history || []);
    } catch (err) {
      console.error("fetchData error:", err);
      setError("Could not connect to the server. Make sure both Flask (port 5000) and Node.js (port 5001) are running.");
    } finally {
      setLoading(false);
    }
  };

  const handleHistoryClick = (item: string) => {
    setQuery(item);
    fetchData(item);
  };

  const interactionResult: InteractionResult | null = userData?.interactionResult ?? null;

  // Build a per-supplement view: group interactions by supplement name
  const buildSupplementMap = () => {
    if (!interactionResult) return [];

    const allSupplements: string[] = interactionResult.input_supplements ?? [];

    return allSupplements.map(supp => {
      const suppNorm = supp.trim().toLowerCase();

      // Find interactions for this supplement
      const found = (interactionResult.interactions ?? []).filter(
        i => i.input_supplement?.trim().toLowerCase() === suppNorm
      );

      // Find no-interactions for this supplement
      const notFound = (interactionResult.no_interactions ?? []).filter(
        i => i.supplement?.trim().toLowerCase() === suppNorm
      );

      return { supplement: supp, interactions: found, noInteractions: notFound };
    });
  };

  const supplementMap = buildSupplementMap();

  // Parse medications and supplements as arrays for display
  const medicationList = userData?.medications
    ? userData.medications.split(",").map((m: string) => m.trim()).filter(Boolean)
    : [];
  const supplementList = userData?.supplements
    ? userData.supplements.split(",").map((s: string) => s.trim()).filter(Boolean)
    : [];
  const allergiesList = userData?.allergies
    ? userData.allergies.split(",").map((a: string) => a.trim()).filter(Boolean)
    : [];

  return (
    <>
      <section className='h-full w-full px-8 py-11 bg-primary-light g-8 column'>

        {/* HEADER */}
        <div className='text-center column g-4'>
          <h1 className='text-primary-dark'>Ayurvedic-Allopathic Drug Interaction Checker</h1>
          <h2 className='text-gray'>Search possible herb-drug interactions</h2>
        </div>

        {/* MAIN CONTENT */}
        <div className='row g-6 desktop'>

          {/* ====== LEFT SIDEBAR ====== */}
          <div className='column w-25p bg-white p-6 r-1 shadow g-4 self-start' style={{ gap: "14px" }}>

            <h3 className='text-primary-dark border-bottom pb-2'>My Registered Profile</h3>

            {!userData ? (
              <p className='text-gray'>Loading...</p>
            ) : (
              <>
                {/* Medications */}
                {medicationList.length > 0 && (
                  <div className='column g-2 border-bottom pb-3'>
                    <p style={{ color: "#888", fontSize: "13px", fontWeight: "600" }}>Medications</p>
                    {medicationList.map((m: string, i: number) => (
                      <p key={i} style={{ fontSize: "13px" }}>• {m}</p>
                    ))}
                  </div>
                )}

                {/* Supplements */}
                {supplementList.length > 0 && (
                  <div className='column g-2 border-bottom pb-3'>
                    <p style={{ color: "#888", fontSize: "13px", fontWeight: "600" }}>Supplements</p>
                    {supplementList.map((s: string, i: number) => (
                      <p key={i} style={{ fontSize: "13px" }}>• {s}</p>
                    ))}
                  </div>
                )}

                {/* Allergies */}
                {allergiesList.length > 0 && (
                  <div className='column g-2 border-bottom pb-3'>
                    <p style={{ color: "#888", fontSize: "13px", fontWeight: "600" }}>Allergies</p>
                    {allergiesList.map((a: string, i: number) => (
                      <p key={i} style={{ fontSize: "13px" }}>• {a}</p>
                    ))}
                  </div>
                )}

                {/* Health Profile */}
                {userData.diseases && (
                  <div className='column g-2 border-bottom pb-3'>
                    <p style={{ color: "#888", fontSize: "13px", fontWeight: "600" }}>Health Profile</p>
                    <p style={{ fontSize: "13px" }}>• {userData.diseases}</p>
                  </div>
                )}

                {/* ====== REGISTERED INTERACTIONS ====== */}
                {interactionResult && (
                  <div className='column g-3'>
                    <p style={{ fontWeight: "700", fontSize: "14px", borderBottom: "1px solid #eee", paddingBottom: "6px" }}>
                      Registered Interactions
                    </p>

                    {supplementMap.length === 0 ? (
                      <p style={{ fontSize: "12px", color: "#38a169" }}>✓ No supplements to check</p>
                    ) : (
                      supplementMap.map((entry, idx) => (
                        <div key={idx} style={{ marginBottom: "8px" }}>

                          {/* ---- Supplement has interactions ---- */}
                          {entry.interactions.length > 0 ? (
                            entry.interactions.map((item, iIdx) => (
                              <div key={iIdx} style={{ marginBottom: "8px" }}>
                                {/* Herb name + badge */}
                                <div style={{ display: "flex", alignItems: "center", gap: "6px", flexWrap: "wrap", marginBottom: "4px" }}>
                                  <p style={{ fontWeight: "600", fontSize: "13px" }}>
                                    • {item.ayurvedic_name}
                                    {item.canonical_name && item.canonical_name !== item.ayurvedic_name
                                      ? ` (${item.canonical_name})`
                                      : ""}
                                  </p>
                                  <SeverityBadge severity={item.interaction_severity} />
                                </div>

                                {/* Drug + effect */}
                                <div style={{ paddingLeft: "12px" }}>
                                  <p style={{ fontSize: "12px", color: "#555", marginBottom: "2px" }}>
                                    • {item.allopathic_drug_name}:
                                  </p>
                                  <p style={{ fontSize: "12px", color: "#333" }}>
                                    {item.clinical_effect || item.recommendation}
                                  </p>
                                </div>
                              </div>
                            ))
                          ) : (
                            /* ---- Supplement has NO interactions ---- */
                            <div style={{ marginBottom: "8px" }}>
                              <div style={{ display: "flex", alignItems: "center", gap: "6px", flexWrap: "wrap", marginBottom: "4px" }}>
                                <p style={{ fontWeight: "600", fontSize: "13px" }}>• {entry.supplement}</p>
                                <span style={{
                                  backgroundColor: "#718096",
                                  color: "white",
                                  padding: "2px 10px",
                                  borderRadius: "12px",
                                  fontSize: "11px",
                                  fontWeight: "bold",
                                  whiteSpace: "nowrap"
                                }}>
                                  No Interaction
                                </span>
                              </div>
                              {entry.noInteractions.length > 0 && (
                                <div style={{ paddingLeft: "12px" }}>
                                  {entry.noInteractions.map((ni, nIdx) => (
                                    <p key={nIdx} style={{ fontSize: "12px", color: "#555" }}>
                                      • {ni.drug}: <span style={{ color: "#888" }}>No interaction found</span>
                                    </p>
                                  ))}
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                      ))
                    )}
                  </div>
                )}
                {/* ====== END INTERACTIONS ====== */}

                <button className='h-3 bg-primary text-white border-none r-2 pointer mt-2'
                  style={{ marginTop: "8px" }}>
                  Edit Profile
                </button>
              </>
            )}
          </div>

          {/* ====== RIGHT CONTENT ====== */}
          <div className='column g-6 w-75p'>

            {/* SEARCH BOX */}
            <div className='shadow border column g-5 p-8 w-100p r-1 bg-white px-8'>
              <h2 className='border-bottom pb-1'>Search Interaction</h2>
              <div className='row flex-wrap g-7'>
                <div className='column g-3 grow shrink input-container'>
                  <label><p>Enter Allopathic Drug Name</p></label>
                  <input
                    className='w-full h-2.5 p-2 r-1 outline-none shadow border'
                    type="text"
                    placeholder="e.g. warfarin, insulin, aspirin, metformin"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    onKeyDown={(e) => { if (e.key === "Enter") fetchData(); }}
                  />
                </div>
                <div className='grow row shrink justify-end input-container'>
                  <button
                    type="button"
                    className='w-50p h-3 bg-primary text-white pointer border-none r-2 mt-7'
                    onClick={() => fetchData()}
                    disabled={loading}
                  >
                    {loading ? "Checking..." : "Check Interaction"}
                  </button>
                </div>
              </div>
            </div>

            {/* ERROR */}
            {error && (
              <div className='column border shadow p-8 w-100p r-1 bg-white'>
                <p style={{ color: "red" }}>{error}</p>
              </div>
            )}

            {/* RESULT */}
            {result && (
              <div className='column border shadow g-5 p-8 w-100p r-1 bg-white'>
                <div className='text-primary-dark-2'>
                  <h2 className='border-bottom pb-1'>Search Result</h2>
                </div>
                <div className='shadow border r-1'>
                  <div className='border-bottom p-5 column g-3'>
                    <h2 className='text-primary-dark-2'>
                      {result.ayurvedic_name} ({result.canonical_name})
                    </h2>
                    <p>
                      System: Ayurveda
                      <span className='text-gray'> | Source: </span>
                      <span className='text-primary-light'>{result.source}</span>
                    </p>
                  </div>
                  <div className='p-5'>
                    <div className='border shadow r-1'>
                      <div className='p-3 border-bottom row justify-between'>
                        <h3 className='text-gray mt-1'>{result.allopathic_drug_name}</h3>
                        <button
                          className='h-2.5 w-8 border-none text-white r-2'
                          style={{ backgroundColor: severityColor(result.interaction_severity) }}
                        >
                          <h3 style={{ textTransform: "capitalize" }}>{result.interaction_severity}</h3>
                        </button>
                      </div>
                      <div className='p-3 column g-3'>
                        <span className='row g-1'>
                          <p><b className='text-primary-dark-2'>Mechanism :</b><span> {result.mechanism}</span></p>
                        </span>
                        <span className='row g-1'>
                          <p><b className='text-primary-dark-2'>Clinical Effect :</b><span> {result.clinical_effect}</span></p>
                        </span>
                        <span className='row g-1'>
                          <p><b className='text-primary-dark-2'>Recommendation :</b><span> {result.recommendation}</span></p>
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* HISTORY */}
            <div className='shadow border column g-5 p-8 w-100p r-1 bg-white'>
              <h2 className='border-bottom pb-1 text-primary-dark-2'>Recent Searches</h2>
              <div className='column g-3 flex-wrap'>
                {history.length === 0 ? (
                  <p className='text-gray'>No recent searches</p>
                ) : (
                  history.map((item, index) => (
                    <p key={index} className='pointer text-primary-dark-2'
                      onClick={() => handleHistoryClick(item)}>
                      &gt; {item}
                    </p>
                  ))
                )}
              </div>
            </div>

            <div className='text-center desktop mt-4'>
              <p className='text-gray'>
                For academic and informational use only. Consult your healthcare provider for professional advice.
              </p>
            </div>

          </div>
        </div>
      </section>
    </>
  );
}

export default Form;