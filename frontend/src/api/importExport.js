import request from './request'

/**
 * 下载 Excel 模板
 */
export function downloadTemplate() {
  return request({
    url: '/import-export/template',
    method: 'get',
    responseType: 'blob'
  })
}

/**
 * 导出数据
 */
export function exportData(params) {
  return request({
    url: '/import-export/export',
    method: 'get',
    params,
    responseType: 'blob'
  })
}
