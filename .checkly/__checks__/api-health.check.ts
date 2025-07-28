import { ApiCheck, AssertionBuilder } from 'checkly/constructs'

new ApiCheck('api-health-check', {
  name: 'API Health Check',
  frequency: 5,
  locations: ['us-east-1', 'eu-west-1'],
  request: {
    url: 'https://quest-omega-wheat.vercel.app/api/health',
    method: 'GET',
    headers: [],
    assertions: [
      AssertionBuilder.statusCode().equals(200),
      AssertionBuilder.jsonBody('$.status').equals('healthy'),
      AssertionBuilder.responseTime().lessThan(1000),
    ],
  },
})