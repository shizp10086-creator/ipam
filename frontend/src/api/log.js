import request from './request'

/**
 * 获取操作日志列表
 */
export function getLogs(params) {
  return request({
    url: '/logs',
    method: 'get',
    params
  })
}

/**
 * 获取日志详情
 */
export function getLog(id) {
  return request({
    url: `/logs/${id}`,
    method: 'get'
  })
}
