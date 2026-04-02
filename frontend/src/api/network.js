import request from './request'

/**
 * 获取网段列表
 */
export function getSegments(params) {
  return request({
    url: '/segments',
    method: 'get',
    params
  })
}

/**
 * 获取网段详情
 */
export function getSegment(id) {
  return request({
    url: `/segments/${id}`,
    method: 'get'
  })
}

/**
 * 创建网段
 */
export function createSegment(data) {
  return request({
    url: '/segments',
    method: 'post',
    data
  })
}

/**
 * 更新网段
 */
export function updateSegment(id, data) {
  return request({
    url: `/segments/${id}`,
    method: 'put',
    data
  })
}

/**
 * 删除网段
 */
export function deleteSegment(id) {
  return request({
    url: `/segments/${id}`,
    method: 'delete'
  })
}

/**
 * 获取网段统计信息
 */
export function getSegmentStats(id) {
  return request({
    url: `/segments/${id}/stats`,
    method: 'get'
  })
}
