/**
 * NewOrderRequestView — submit a new production order request (external client).
 */
import React from 'react';
import RequestForm from '../components/RequestForm';

interface NewOrderRequestViewProps {
  onSubmitted: () => void;
}

const NewOrderRequestView: React.FC<NewOrderRequestViewProps> = ({ onSubmitted }) => (
  <RequestForm kind="order" onSubmitted={onSubmitted} />
);

export default NewOrderRequestView;
