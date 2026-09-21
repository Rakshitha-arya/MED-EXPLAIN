import React from 'react';

export const DISCLAIMER_TEXT =
  'This system is for educational purposes only. It helps explain information contained in medical reports and does not provide a medical diagnosis or treatment recommendation. Consult a qualified healthcare professional for medical advice.';

export default function Disclaimer({ customText }) {
  return (
    <div className="disclaimer-banner" role="note">
      <span className="disclaimer-icon">⚠️</span>
      <div>
        <strong>Educational Disclaimer: </strong>
        {customText || DISCLAIMER_TEXT}
      </div>
    </div>
  );
}
