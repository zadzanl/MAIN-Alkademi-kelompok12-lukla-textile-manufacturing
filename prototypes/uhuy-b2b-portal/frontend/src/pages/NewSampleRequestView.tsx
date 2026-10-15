/**
 * NewSampleRequestView — submit a new design/sample request (external client).
 */
import React from 'react';
import RequestForm from '../components/RequestForm';

interface NewSampleRequestViewProps {
  onSubmitted: () => void;
}

const NewSampleRequestView: React.FC<NewSampleRequestViewProps> = ({ onSubmitted }) => (
  <RequestForm kind="sample" onSubmitted={onSubmitted} />
);

export default NewSampleRequestView;
