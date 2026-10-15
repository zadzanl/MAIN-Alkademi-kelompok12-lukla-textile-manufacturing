import yaml

def main():
    with open('openspec/changes/reconcile-openapi-endpoint-gaps/artifacts/reference-draft-openapi.yaml', encoding='utf-8') as f:
        d = yaml.safe_load(f)

    paths = [
        ('/sewing-tallies', 'get'),
        ('/cut-batches', 'get'),
        ('/orders/{orderId}/confirmation', 'post'),
        ('/orders/{orderId}/cancellation', 'post'),
        ('/purchase-orders', 'get'),
        ('/purchase-orders/{purchaseOrderId}', 'get'),
        ('/supplier-invoices', 'get'),
        ('/client-invoices/{invoiceId}', 'get'),
        ('/ledger/accounts', 'get'),
        ('/ledger/transactions/{transactionId}', 'get'),
        ('/clients/{clientId}', 'get'),
        ('/samples/{sampleId}', 'get'),
        ('/assemblies/{assemblyId}', 'get'),
        ('/time-studies', 'get'),
        ('/assemblies', 'get'),
    ]

    for p, m in paths:
        op = d['paths'].get(p, {}).get(m, {})
        op_id = op.get('operationId')
        params = []
        for param in op.get('parameters', []):
            if '$ref' in param:
                params.append(param['$ref'].split('/')[-1])
            else:
                p_in = param.get('in')
                p_name = param.get('name')
                p_req = param.get('required', False)
                p_type = param.get('schema', {}).get('type', param.get('schema', {}).get('$ref', 'unknown'))
                params.append(f"{p_name} ({p_in}, req={p_req}, type={p_type})")
        print(f"{m.upper():4} {p:42} [{op_id}]:")
        for pr in params:
            print(f"    - {pr}")

if __name__ == '__main__':
    main()
