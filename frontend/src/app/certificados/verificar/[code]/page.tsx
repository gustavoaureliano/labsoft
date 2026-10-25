import { LearningPageShell } from "@/components/layout/LearningPageShell";
import { CertificateVerification } from "@/components/learning/Certificates";

export default async function VerifyCertificatePage({params}: {params: Promise<{code: string}>}) {
  const {code} = await params;
  return <LearningPageShell><CertificateVerification code={code} /></LearningPageShell>;
}
