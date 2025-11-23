import React from 'react';
import { TermSheetGenerator } from '../components/TermSheetGenerator';
import MainLayout from '../layouts/MainLayout';

export default function TermSheet() {
  return (
    <MainLayout activeModule="term-sheet">
      <TermSheetGenerator />
    </MainLayout>
  );
}

