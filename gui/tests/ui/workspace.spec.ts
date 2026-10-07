import {test,expect} from '@playwright/test';
import fs from 'node:fs';
fs.mkdirSync('.runtime/screenshots',{recursive:true});
test('real baseline loads and navigation exposes the model and dataset',async({page})=>{
 await page.goto('/');await expect(page.getByRole('heading',{name:'Your sleep research workspace'})).toBeVisible();await expect(page.getByText('61.99%',{exact:true})).toBeVisible();await page.screenshot({path:'.runtime/screenshots/browser-overview.png',fullPage:true});
 await page.getByRole('button',{name:'Model details',exact:true}).click();await expect(page.getByRole('heading',{name:'Meet the model'})).toBeVisible();await expect(page.getByText('226,309',{exact:true})).toBeVisible();
 await page.getByRole('button',{name:'Dataset details',exact:true}).click();await expect(page.getByRole('heading',{name:'Inside the dataset'})).toBeVisible();await expect(page.getByText('22,608',{exact:true}).first()).toBeVisible();
});
test('results show actual epochs, uncertainty, evaluations and searchable artifacts',async({page})=>{
 await page.goto('/');await page.getByRole('button',{name:'Results explorer',exact:true}).click();await page.getByRole('button',{name:'EEG & hypnogram',exact:true}).click();await expect(page.getByRole('img',{name:'Normalized EEG waveform'})).toBeVisible();
 await page.getByRole('button',{name:'Next epoch'}).click();await expect(page.getByText('No EEG samples cached for this epoch.')).toBeVisible();
 await page.getByRole('button',{name:'Evaluation',exact:true}).click();await expect(page.getByRole('heading',{name:'Confusion matrix'})).toBeVisible();await expect(page.getByText('61.99%',{exact:true}).first()).toBeVisible();
 await page.getByRole('button',{name:/^Artifacts/}).click();await page.getByRole('textbox',{name:'Search artifacts'}).fill('overall_metrics');await page.getByRole('button',{name:'overall_metrics.json',exact:true}).click();await expect(page.getByRole('dialog',{name:'Artifact preview'})).toBeVisible();await expect(page.getByRole('dialog').getByText(/0.619931/)).toBeVisible();
});
test('recording selection and workspace search work without pretending to run Colab',async({page})=>{
 await page.goto('/');await page.getByRole('button',{name:'Data & Run',exact:true}).click();await expect(page.getByRole('button',{name:/SN009/})).toBeVisible();await page.getByRole('button',{name:/SN001/}).click();
 await page.getByRole('button',{name:'Run analysis',exact:true}).click();await expect(page.getByRole('status')).toContainText('desktop app');
 await page.getByRole('textbox',{name:'Search workspace'}).fill('model');await page.getByRole('button',{name:'Model details Screen'}).click();await expect(page.getByRole('heading',{name:'Meet the model'})).toBeVisible();
 await page.getByRole('button',{name:'Toggle color theme'}).click();await expect(page.locator('html')).toHaveAttribute('data-theme','light');
});
