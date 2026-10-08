import { describe,it,expect } from 'vitest';
import { render,screen,cleanup } from '@testing-library/react';
import { DataTable } from './DataTable';
describe('DataTable',()=>{
 it('explains empty results',()=>{render(<DataTable rows={[]} columns={['name']}/>);expect(screen.getByText(/No records available/)).toBeInTheDocument();cleanup();});
 it('renders accessible headers and actual values',()=>{render(<DataTable rows={[{name:'orders',count:42}]} columns={['name','count']}/>);expect(screen.getAllByRole('columnheader')).toHaveLength(2);expect(screen.getByText('42')).toBeInTheDocument();cleanup();});
});
