"use client";

import React from "react";
import { WizardProvider } from "@/context/WizardContext";
import { WizardWorkflow } from "@/components/wizard/WizardWorkflow";

export default function WizardPage() {
  return (
    <WizardProvider>
      <WizardWorkflow />
    </WizardProvider>
  );
}
