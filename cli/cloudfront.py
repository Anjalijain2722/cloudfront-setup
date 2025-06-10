def create_distribution(session, origin_domain_name):
    cf = session.client('cloudfront')
    distribution_config = {
        'CallerReference': str(hash(origin_domain_name)),
        'Origins': {
            'Quantity': 1,
            'Items': [{
                'Id': 'origin1',
                'DomainName': origin_domain_name,
                'OriginPath': '',
                'CustomOriginConfig': {
                    'HTTPPort': 80,
                    'HTTPSPort': 443,
                    'OriginProtocolPolicy': 'http-only'
                }
            }]
        },
        'DefaultCacheBehavior': {
            'TargetOriginId': 'origin1',
            'ViewerProtocolPolicy': 'allow-all',
            'TrustedSigners': {
                'Enabled': False,
                'Quantity': 0
            },
            'ForwardedValues': {
                'QueryString': False,
                'Cookies': {'Forward': 'none'}
            },
            'DefaultTTL': 86400,
            'MinTTL': 0,
            'MaxTTL': 31536000
        },
        'Comment': 'Created by automation',
        'Enabled': True
    }

    response = cf.create_distribution(DistributionConfig=distribution_config)
    distribution_id = response['Distribution']['Id']
    return distribution_id
