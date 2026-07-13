import { Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import About from "./pages/About";
import Compare from "./pages/Compare";
import DiseaseDetail from "./pages/DiseaseDetail";
import GapReviewQueue from "./pages/GapReviewQueue";
import GeneDetail from "./pages/GeneDetail";
import ProgramDetailPage from "./pages/ProgramDetail";
import Programs from "./pages/Programs";
import Search from "./pages/Search";

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Search />} />
        <Route path="/gene/:geneId" element={<GeneDetail />} />
        <Route path="/disease/:diseaseId" element={<DiseaseDetail />} />
        <Route path="/compare" element={<Compare />} />
        <Route path="/programs" element={<Programs />} />
        <Route path="/program/:programId" element={<ProgramDetailPage />} />
        <Route path="/gaps/review" element={<GapReviewQueue />} />
        <Route path="/about" element={<About />} />
      </Routes>
    </Layout>
  );
}
